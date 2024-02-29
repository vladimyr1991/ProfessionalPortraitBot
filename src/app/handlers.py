from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, BotCommand
from . import keyboards as kb
from aiohttp import ClientSession
import os


TOKEN: str = os.environ.get("TOKEN")

router = Router()


async def download_photo(file_id, save_path, bot):
    async with ClientSession() as session:
        file = await bot.get_file(file_id)
        file_path = file.file_path
        download_url = f'https://api.telegram.org/file/bot{TOKEN}/{file_path}'

        async with session.get(download_url) as response:
            if response.status == 200:
                with open(save_path, 'wb') as f:
                    while True:
                        chunk = await response.content.read(1024)
                        if not chunk:
                            break
                        f.write(chunk)
                print(f'Photo saved to {save_path}')


@router.message(CommandStart())
async def cmd_start(message: Message):
    # TODO:
    # нужно сделать хорошее описание и добавить примеров фотографий
    welcome_message = """
    🌟 Добро пожаловать в @ProfessionalPortraitBot, вашего помощника в создании деловых портретов! 🌟
    \nС ProfessionalPortraitBot вы можете легко преобразовать свои фотографии в профессиональные деловые портреты. 
    \nВсё, что вам нужно, это: 
    - загрузить своё фото
    - оплатить услугу
    - дождаться готовности и получить свои портреты
    \n Повысьте свой профессиональный имидж с ProfessionalPortraitBot уже сегодня!
    """
    await message.answer(welcome_message, reply_markup=kb.main)


@router.message(F.text == "Заказать портрет")
async def order_portrait(message: Message):
    await message.answer("Загрузите 11 фотографий с вашим изображением через добавление фото.")


@router.message(F.photo)
async def add_photo(message: Message, bot: BotCommand):
    file_id = message.photo[-1].file_id  # Get the file_id of the photo
    save_path = f'./app/photos/{file_id}.jpg'
    await download_photo(file_id, save_path, bot)
    await message.answer("Фото загружено")
