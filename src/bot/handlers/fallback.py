from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from bot.states.photo_session import PhotoSessionStates

router = Router()

# ⚠️ If user is in photo uploading state and sends a document (e.g., .webp file)
@router.message(PhotoSessionStates.uploading_photos, F.document)
async def handle_document_in_upload(message: Message):
    file_name = message.document.file_name.lower()
    if file_name.endswith(".webp"):
        await message.answer(
            "⚠️ WEBP format is not supported for photo uploads.\n"
            "Please send your photo in JPG or PNG format."
        )
    else:
        await message.answer(
            "📄 You've sent a file. Please make sure to send your photo as an image, not as a document."
        )

@router.message(PhotoSessionStates.uploading_photos, F.sticker)
async def handle_webp_sticker_upload(message: Message):
    await message.answer(
        "🧃 It looks like you sent a sticker (.webp).\n"
        "Unfortunately, stickers can't be used to train your model.\n\n"
        "📸 Please send real photos in JPG or PNG format."
    )

# 🎞️ If user sends an animation (GIF or similar)
@router.message(PhotoSessionStates.uploading_photos, F.animation)
async def handle_animation_in_upload(message: Message):
    await message.answer("🎞️ I can't process animated images. Please send static JPG or PNG photos.")

# 🔍 Catch any other message type while uploading
@router.message(PhotoSessionStates.uploading_photos)
async def handle_unknown_upload(message: Message):
    await message.answer("❗ I couldn't recognize that as a photo.\nPlease send a JPG or PNG image.")

# 🤖 Global fallback for unknown messages outside upload flow
@router.message()
async def global_fallback_handler(message: Message, state: FSMContext):
    await message.answer("🤖 I didn’t quite get that.\nPlease use the menu buttons to interact with me.")
