from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters import RegexpCommandsFilter
from aiogram.dispatcher.filters import Text as TextFilter
from aiogram.types.input_media import InputMediaDocument, MediaGroup
from aiogram.types.message import ContentType, ParseMode

from app import exceptions, file_service, keyboards, resources
from app import service as bot_service
from app.logger import logger
from app.settings import BOT_TOKEN
from app.states import DeleteCategoryState, GetCategoryState, UploadStates

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


@dp.message_handler(commands=["start"])
async def send_welcome(message):
    await message.answer(
        resources.START_MESSAGE,
        reply_markup=keyboards.main_keyboard,
    )


@dp.message_handler(content_types=[ContentType.DOCUMENT])
async def handle_file_message(message):
    await UploadStates.handle_documents_or_category.set()
    state = Dispatcher.get_current().current_state()
    if message.document:
        await state.update_data(documents=[message.document])
    else:
        message.answer("Not supported")
        state.reset_state()

    user_id = message.from_user.id
    categories = file_service.get_user_categories(user_id=user_id)
    keyboard = keyboards.create_categories_keboard(categories=categories)
    await bot_service.send_message_about_documents_save(message, keyboard)


@dp.message_handler(
    content_types=[ContentType.DOCUMENT],
    state=UploadStates.handle_documents_or_category,
)
async def handle_additional_document_to_save(message, state):
    """Обработка дополнительного файла к сохранению"""
    async with state.proxy() as data:  # type: dict
        if message.document:
            data["documents"].append(message.document)

    await message.delete()
    await message.answer("Добавлено к сохранению")


@dp.callback_query_handler(state=UploadStates.handle_documents_or_category)
async def handle_documents_or_category(call, state):
    await call.message.delete()  # удаляем клавиатуру

    if call.data == keyboards.EXTRA_CATEGORY:
        await call.message.answer("Введите название категории:")
        await UploadStates.next()
        return

    async with state.proxy() as data:
        documents = data.get("documents", None)
        user_id = call.from_user.id
        category = call.data

    await state.finish()
    if documents:
        await save_documents(documents, user_id, category, call.message)


@dp.message_handler(state=UploadStates.handle_new_category)
async def handle_new_category(message, state):
    """Обработка новой категории.

    Пользователь ввёл новую категорию - проверка на правильность
    названия категории, и сохранение файла в данной категории
    """
    if message.text.strip() == keyboards.EXTRA_CATEGORY:
        await message.answer(resources.INCORRECT_CATEGORY_NAME)
        return

    user_id = message.from_user.id
    category = message.text.strip()

    async with state.proxy() as data:
        docs = data.get("documents", None)
        if docs:
            await save_documents(docs, user_id, category, message)

    await state.finish()


async def save_documents(documents, user_id, category, message):
    """Сохранение переданных файлов.

    Сохраняем переданные файлы и сообщаем, сколько из них сохранилось
    (возможно пользователь отправил файлы, которые уже были загружены ранее)
    """
    all_files_saved = True
    any_files_saved = False

    for document in documents:
        try:
            file_service.save_telegram_document(document, user_id, category)
        except exceptions.FileAlreadyExists:
            filename = document.file_name
            await message.answer(f"{filename} уже сохранён")
            all_files_saved = False
        else:
            any_files_saved = True

    await send_message_how_many_documents_was_saved(
        all_files_saved, any_files_saved, message
    )


async def send_message_how_many_documents_was_saved(
    all_files_saved, any_files_saved, message
):
    """Отправляем информацию о том, сколько файлов было сохранено"""
    if all_files_saved:
        await message.answer("Все файлы сохранены!")
    elif any_files_saved:
        # если какой-то файл не был сохранён, то было
        # отправлено сообщение вида "<document> уже сохранён",
        # поэтому используется слово "остальные"
        await message.answer("Остальные файлы сохранены!")
    else:
        await message.answer("Ни один файл не сохранён!")


@dp.message_handler(TextFilter(equals=keyboards.MY_FILES))
async def send_owned_files(message):
    """Обработка команды "Мои файлы".

    Отправляем пользователю информацию о его загруженных файлах.
    """
    user_id = message.from_user.id
    answer_message = generate_owned_files_answer(user_id)
    await message.answer(answer_message, parse_mode=ParseMode.MARKDOWN)


def generate_owned_files_answer(user_id):
    """Генерация ответа для команды "Мои файлы".

    Генерируем ответ с файлами пользователя, сгруппироваными
    по категориям. Если файлов нет, то возвращаем сообщение,
    что у пользователя нет загруженных файлов
    """
    try:
        files = file_service.get_owned_files(user_id)
    except exceptions.NoUserFiles as e:
        return str(e)
    else:
        grouped_files = file_service.group_files_by_category(files)
        text = resources.generate_grouped_files_text(grouped_files)
        return text


@dp.message_handler(TextFilter(equals=keyboards.GET_CATEGORY_FILES))
async def handle_get_category_files(message):
    """Обработка команды "Получить категорию".

    Отправляем клавиатуру с выбором категории файлов, если таковые
    есть, иначе сообщаем, что у пользователя нет файлов
    """
    user_id = message.from_user.id
    categories = file_service.get_user_categories(user_id)
    if not categories:
        await message.answer("У вас пока нет ни одного файла")
        return

    await GetCategoryState.handle_category.set()
    keyboard = keyboards.create_categories_get_keyboard(categories)
    await message.answer(
        "Выберите категорию для получения:",
        reply_markup=keyboard,
    )


@dp.callback_query_handler(state=GetCategoryState.handle_category)
async def handle_category_to_get(call, state):
    """Обработка выбранной для получения файлов категории"""
    await call.message.delete()  # удаляем клавитуру

    if call.data == keyboards.CANCEL_GETTING:
        await state.finish()
        return

    category = call.data
    user_id = call.from_user.id
    files = file_service.get_category_files(category, user_id)
    await send_files(files, call.message)
    await state.finish()


async def send_files(files, message):
    """Отправка файлов пользователю.

    Отправляем пользователю файлы как группу файлов
    """
    media_group = MediaGroup()
    attachments = (InputMediaDocument(f.file_id) for f in files)
    media_group.attach_many(*attachments)
    await message.answer_media_group(media_group)


@dp.message_handler(TextFilter(equals=keyboards.DELETE_CATEGORY_FILES))
async def handle_delete_category_files(message):
    """Обработка команды "Удалить категорию".

    Если у пользователя есть файлы, то отправляем клавиатуру
    с выбором категории для удаления и кнопкой отмены действия.
    Если же у пользователя нет файлов, то уведомляем его об этом
    """
    user_id = message.from_user.id
    categories = file_service.get_user_categories(user_id)
    if not categories:
        await message.answer("У вас нет категорий для удаления")
        return

    await DeleteCategoryState.handle_category.set()
    keyboard = keyboards.create_categories_delete_keyboard(categories)
    await message.answer(
        "Выберите категорию для удаления:",
        reply_markup=keyboard,
    )


@dp.callback_query_handler(state=DeleteCategoryState.handle_category)
async def handle_category_to_delete(call, state):
    """Обработка выбранной для удаления категории"""
    await call.message.delete()  # удаляем клавитуру

    if call.data == keyboards.CANCEL_DELETION:
        await state.finish()
        return

    category = call.data
    user_id = call.from_user.id
    file_service.delete_category_files(category, user_id)

    await call.message.answer(f"Категория {category} успешно удалена")
    await state.finish()


@dp.message_handler(RegexpCommandsFilter(regexp_commands=[r"f(\d*)"]))
async def handle_get_file_command(message, regexp_command):
    """Обработка команды /f<unique_id>.

    Обрабатываем команду получения файла по его ID.
    Если файл с таким ID существует, и он принадлежит данному
    пользователю, то отправляем его
    """
    unique_id = int(regexp_command.group(1))
    user_id = message.from_user.id
    try:
        file = file_service.get_file(unique_id, user_id)
    except exceptions.IncorrectFileID as e:
        await message.answer(str(e))
    else:
        await message.answer_document(file.file_id)


@dp.message_handler(RegexpCommandsFilter(regexp_commands=[r"d(\d*)"]))
async def handle_delete_file_command(message, regexp_command):
    """Обработка команды /d<unique_id>.

    Обрабатываем команду удаления файла по его ID.
    Если пользователь имеет доступ к данному файлу, то
    удалаяем файл, иначе отправляем сообщение, что нет доступа
    """
    unique_id = int(regexp_command.group(1))
    user_id = message.from_user.id
    try:
        file_service.delete_file(unique_id, user_id)
    except exceptions.IncorrectFileID as e:
        await message.answer(str(e))
    else:
        await message.answer("Успешно удалено!")


@dp.errors_handler()
async def handle_errors(update, error):
    """Обработка непредвиденных ошибок.

    Логируем ошибку, а также отправляем пользователю
    сообщение, что произошла непредвиденная ошибка
    """
    message = update.message or update.callback_query.message
    await message.answer("Произошла ошибка")
    logger.exception("Exception occured!")
    return True
