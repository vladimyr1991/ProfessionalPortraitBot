from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.handlers.main_menu import show_main_menu

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    await show_main_menu(message, state)
