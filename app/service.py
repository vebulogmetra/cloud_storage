async def send_message_about_documents_save(message, keyboard):
    await message.answer(
        "Вы можете отправить ещё файлы, либо выбрать категорию:",
        reply_markup=keyboard,
    )
