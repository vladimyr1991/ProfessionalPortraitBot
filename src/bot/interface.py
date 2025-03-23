import asyncio
import os
import time

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, KeyboardButton, ReplyKeyboardMarkup, BufferedInputFile

from .logic import generate_ai_photo

API_TOKEN = os.environ.get("BOT_TOKEN")

# Use FSM memory storage
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


# FSM states
class PhotoSessionStates(StatesGroup):
    free_prompting = State()


# Main menu keyboard
def main_menu_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🆓 Free Prompting", callback_data="free_prompting")],
            ]
        )


# Back button
def back_menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔙 Back to Main Menu")]
            ],
        resize_keyboard=True,
        one_time_keyboard=True
        )


@dp.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    """Processes /start command"""
    await state.clear()
    await message.answer("👋 Welcome! Choose your AI photo style:", reply_markup=main_menu_kb())


@dp.callback_query(F.data == "free_prompting")
async def handle_free_prompting(callback: CallbackQuery, state: FSMContext):
    """Handles free prompting selection"""
    await state.set_state(PhotoSessionStates.free_prompting)
    await callback.message.answer(
        "📝 Please input your prompt for the AI photo session.",
        reply_markup=back_menu_kb()
        )
    await callback.answer()


@dp.message(F.text == "🔙 Back to Main Menu")
async def back_to_menu_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🔙 Back to main menu:", reply_markup=main_menu_kb())


@dp.message(PhotoSessionStates.free_prompting)
async def prompt_input_handler(message: Message, state: FSMContext):
    prompt_text = message.text

    loading_msg = await message.answer("⌛ Generating your AI photo... please wait...")
    start_time = time.time()
    try:
        image_bytes = await generate_ai_photo(prompt_text)

        if image_bytes:
            photo = BufferedInputFile(image_bytes, filename="ai_photo.png")
            elapsed = time.time() - start_time
            await message.answer_photo(photo=photo, caption=f"✨ Here's your generated photo!\n⏱️ Took {elapsed:.1f} seconds")
        else:
            await message.answer("❌ Failed to generate photo. Please try again later.")
    except Exception as e:
        await message.answer("🚨 An error occurred while generating the image.")
        print(f"Error: {e}")
    try:
        await loading_msg.delete()
    except Exception:
        pass  # in case it was already deleted or too late
    await message.answer("🔄 Send another prompt or return to menu:", reply_markup=back_menu_kb())


async def run():
    bot = Bot(token=API_TOKEN)
    await dp.start_polling(bot)