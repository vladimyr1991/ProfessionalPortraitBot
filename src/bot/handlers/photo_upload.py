from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards.back_button import back_menu_kb
from bot.keyboards.done_button import done_uploading_kb
from bot.states.photo_session import PhotoSessionStates

router = Router()


@router.callback_query(F.data == "model_free_prompting")
async def train_personal_model(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(PhotoSessionStates.uploading_photos)
    await state.update_data(photo_count=0)

    part_1 = (
        "📸 <b>Let’s create your AI model!</b>\n\n"
        "To generate realistic photos of you, we first need to teach the AI what you look like.\n\n"
        "✅ Please upload <b>at least 5 high-quality photos</b> of yourself.\n"
        "🔝 For best results, send <b>15–20 photos</b> with:\n"
        "• Only <b>you</b> in the frame (no other people)\n"
        "• <b>Different angles</b>, expressions, and backgrounds\n"
    )

    part_2 = (
        "• <b>Clear lighting</b>, no heavy filters or distortions\n\n"
        "Once your model is ready, you’ll be able to generate awesome AI-styled portraits in various looks! 🎨✨\n\n"
        "When you're ready — just start sending your photos one by one 📥"
    )

    await callback.message.answer(part_1, parse_mode="HTML")
    await callback.message.answer(part_2, reply_markup=back_menu_kb(), parse_mode="HTML")
    await callback.answer()


@router.message(PhotoSessionStates.uploading_photos, F.photo)
async def handle_uploaded_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    count = data.get("photo_count", 0) + 1
    await state.update_data(photo_count=count)

    await message.answer(f"📷 Photo {count} received!", reply_markup=done_uploading_kb())

    if count == 5:
        await message.answer("✅ Minimum reached! You can continue uploading more for better results.")
    elif count == 20:
        await message.answer("🚀 You've hit the max recommended number! Feel free to press '✅ Done Uploading' when ready.")


@router.callback_query(F.data == "finish_uploading")
async def handle_finish_uploading(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    count = data.get("photo_count", 0)

    if count < 5:
        await callback.message.answer(f"⚠️ You’ve uploaded only {count} photo(s). Please upload at least 5 for good results.")
    else:
        await callback.message.answer("🛠️ Creating your model... This might take a minute. Please wait ⏳")
        # 🔧 Placeholder for model training logic
        await state.clear()

    await callback.answer()
