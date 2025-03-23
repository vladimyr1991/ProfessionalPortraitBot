import os
import time

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards.back_button import back_menu_kb
from bot.keyboards.done_button import done_uploading_kb
from bot.services.model_trainer import train_user_model_pipeline
from bot.states.photo_session import PhotoSessionStates

router = Router()

ALLOWED_FORMATS = ('.jpg', '.jpeg', '.png')


@router.callback_query(F.data == "model_free_prompting")
async def train_personal_model(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    save_dir = f"media/{user_id}/raw_photos"
    os.makedirs(save_dir, exist_ok=True)

    # Count existing photos
    image_count = len(
        [
            f for f in os.listdir(save_dir)
            if f.lower().endswith((".jpg", ".jpeg", ".png"))
            ]
        )

    await state.set_state(PhotoSessionStates.uploading_photos)
    await state.update_data(photo_count=image_count)

    if image_count >= 5:
        await callback.message.answer(
            f"📁 You already have {image_count} saved photos.\n"
            "You can upload more if you'd like — or just press ✅ Done Uploading to continue.",
            reply_markup=done_uploading_kb()
            )
    else:
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


@router.message(PhotoSessionStates.uploading_photos, F.document)
async def handle_unsupported_document(message: Message):
    file_name = message.document.file_name.lower()
    if file_name.endswith((".webp", ".heic", ".gif", ".bmp", ".tiff")):
        await message.answer("❌ Unsupported image format. Please send only JPG, JPEG, or PNG files.")
    else:
        await message.answer("📄 You've sent a file. If it's a photo, please send it as an image (not as a document).")


@router.message(F.document)
async def debug_document_handler(message: Message):
    await message.answer(f"📄 Got document: {message.document.file_name}")


@router.message(PhotoSessionStates.uploading_photos, F.photo)
async def handle_uploaded_photo(message: Message, state: FSMContext):
    user_id = message.from_user.id
    print(">> Photo handler triggered")

    # Get the highest-quality photo version
    photo = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)
    file_path = file.file_path

    ext = os.path.splitext(file_path)[1].lower()

    if ext not in ALLOWED_FORMATS:
        await message.answer("❌ Unsupported image format. Please send only JPG, JPEG, or PNG files.")
        return

    # Download file
    file_bytes = await message.bot.download_file(file_path)

    # Create user-specific folder
    save_dir = f"media/{user_id}/raw_photos"
    os.makedirs(save_dir, exist_ok=True)

    # Generate a filename with timestamp
    filename = f"{int(time.time())}.jpg"
    full_path = os.path.join(save_dir, filename)

    # Save to disk
    with open(full_path, "wb") as f:
        f.write(file_bytes.getvalue())

    # Get amount of uploaded images
    count = len(
        [
            f for f in os.listdir(save_dir)
            if os.path.isfile(os.path.join(save_dir, f)) and f.lower().endswith((".jpg", ".jpeg", ".png"))
            ]
        )
    await state.update_data(photo_count=count)

    await message.answer(f"📷 Photo {count} received and saved!", reply_markup=done_uploading_kb())

    if count == 5:
        await message.answer("✅ Minimum reached! You can continue uploading more for better results.")
    elif count == 20:
        await message.answer("🚀 You've hit the max recommended number! Feel free to press '✅ Done Uploading' when ready.")


@router.callback_query(F.data == "finish_uploading")
async def handle_finish_uploading(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    save_dir = f"media/{user_id}/raw_photos"

    # Check how many real photos exist
    image_count = len([
        f for f in os.listdir(save_dir)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ])

    if image_count < 5:
        await callback.message.answer(
            f"⚠️ You’ve uploaded only {image_count} photo(s).\n"
            "Please upload at least 5 for good results."
        )
        await callback.answer()
        return

    await callback.message.answer("🛠️ Starting your model training... please wait ⏳")
    await state.clear()

    # Call the actual training logic
    success = await train_user_model_pipeline(user_id, save_dir)

    if success:
        await callback.message.answer("✅ Your model has been successfully trained! You can now generate images.")
        # Optionally: Show "Generate with Prompt" button here
    else:
        await callback.message.answer("❌ Something went wrong during training. Please try again later.")

    await callback.answer()
