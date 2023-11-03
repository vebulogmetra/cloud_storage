from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

EXTRA_CATEGORY = "Добавить категорию"
CANCEL_GETTING = CANCEL_DELETION = "Отмена"


def create_categories_keboard(categories: list[str]):
    keyboard = InlineKeyboardMarkup()
    buttons = (*categories, EXTRA_CATEGORY)
    _add_inline_buttons(keyboard, buttons)
    return keyboard


def create_categories_get_keyboard(categories):
    keyboard = InlineKeyboardMarkup()
    buttons = (*categories, CANCEL_GETTING)
    _add_inline_buttons(keyboard, buttons)
    return keyboard


def create_categories_delete_keyboard(categories):
    keyboard = InlineKeyboardMarkup()
    buttons = (*categories, CANCEL_DELETION)
    _add_inline_buttons(keyboard, buttons)
    return keyboard


def _add_inline_buttons(keyboard, button_texts):
    for text in button_texts:
        keyboard.add(InlineKeyboardButton(text, callback_data=text))


MY_FILES = "Мои файлы"
GET_CATEGORY_FILES = "Получить категорию"
DELETE_CATEGORY_FILES = "Удалить категорию"


main_keyboard = ReplyKeyboardMarkup(
    [
        [KeyboardButton(MY_FILES)],
        [KeyboardButton(GET_CATEGORY_FILES)],
        [KeyboardButton(DELETE_CATEGORY_FILES)],
    ],
    resize_keyboard=True,
)
