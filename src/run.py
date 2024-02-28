import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from app.handlers import router
from app.database.models import async_main
from app import TOKEN


async def main():
    await async_main()
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_router(router=router)
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("interrupted")
