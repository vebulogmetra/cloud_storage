from aiogram.dispatcher.filters.state import State, StatesGroup


class UploadStates(StatesGroup):
    handle_documents_or_category = State()
    handle_new_category = State()


class GetCategoryState(StatesGroup):
    handle_category = State()


class DeleteCategoryState(StatesGroup):
    handle_category = State()
