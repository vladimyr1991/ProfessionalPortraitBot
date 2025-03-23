import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
import bot

API_TOKEN = os.environ.get("BOT_TOKEN")

storage = MemoryStorage()
dp = Dispatcher(storage=storage)


if __name__ == '__main__':
    asyncio.run(bot.run())
