from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from . import keyboards as kb

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    # TODO:
    # нужно сделать хорошее описание и добавить примеров фотографий
    welcom_message = """
    🌟 Добро пожаловать в @ProfessionalPortraitBot, вашего помощника в создании деловых портретов! 🌟
    \nС ProfessionalPortraitBot вы можете легко преобразовать свои фотографии в профессиональные деловые портреты. 
    \nВсё, что вам нужно, это: 
    - загрузить своё фото
    - оплатить услугу
    - дождаться готовности
    \n Повысьте свой профессиональный имидж с ProfessionalPortraitBot уже сегодня!
    """
    await message.answer(welcom_message, reply_markup=kb.main)


@router.message(F.text == "Сгенерировать профессиональное фото")
async def create_order(message: Message):
    await message.reply("В")
