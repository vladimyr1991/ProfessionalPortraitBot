from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.keyboards.main_menu import main_menu_kb

router = Router()


# ✅ Reusable function
async def show_main_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("👋 Welcome! Choose your AI photo style:", reply_markup=main_menu_kb())


# 🔁 Triggered when user presses "Back"
@router.message(F.text == "🔙 Back to main menu:")
async def back_to_menu_handler(message: Message, state: FSMContext):
    await show_main_menu(message, state)
