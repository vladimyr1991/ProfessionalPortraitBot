import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from bot.handlers import start, free_prompting, photo_upload, back_to_menu, main_menu
from shared.errors import TelegramAPIKeyError

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    TelegramAPIKeyError("Token not found.")


def register_handlers(dp: Dispatcher):
    dp.include_router(start.router)
    dp.include_router(free_prompting.router)
    dp.include_router(photo_upload.router)
    dp.include_router(back_to_menu.router)
    dp.include_router(main_menu.router)


async def run():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    register_handlers(dp)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(run())
