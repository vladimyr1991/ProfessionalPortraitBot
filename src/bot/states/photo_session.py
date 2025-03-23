from aiogram.fsm.state import State, StatesGroup


class PhotoSessionStates(StatesGroup):
    free_prompting = State()
    uploading_photos = State()
