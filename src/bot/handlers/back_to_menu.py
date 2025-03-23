from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.handlers.main_menu import show_main_menu

router = Router()


@router.message(F.text == "🔙 Back to Main Menu")
async def back_to_menu_handler(message: Message, state: FSMContext):
    await state.clear()
    await show_main_menu(message, state)
