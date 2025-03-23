import time

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, BufferedInputFile

from bot.keyboards.back_button import back_menu_kb
from bot.services.ai_photo_generator import generate_ai_photo
from bot.states.photo_session import PhotoSessionStates

router = Router()


@router.callback_query(F.data == "free_prompting", ~F.text.in_({"🔙 Back to Main Menu"}))
async def handle_free_prompting(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PhotoSessionStates.free_prompting)
    await callback.message.answer("📝 Please input your prompt for the AI photo session.", reply_markup=back_menu_kb())
    await callback.answer()


@router.message(PhotoSessionStates.free_prompting, ~F.text.in_({"🔙 Back to Main Menu"}))
async def prompt_input_handler(message: Message, state: FSMContext):
    prompt_text = message.text
    loading_msg = await message.answer("⌛ Generating your AI photo... please wait...")
    start_time = time.time()
    try:
        image_bytes = await generate_ai_photo(prompt_text)
        image_bytes = None
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
        pass
    await message.answer("🔄 Send another prompt or return to menu:", reply_markup=back_menu_kb())
