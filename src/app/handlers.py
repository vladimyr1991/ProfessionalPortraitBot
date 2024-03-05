from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from asyncio import Lock
from . import keyboards as kb
from .database import create_user, user_registered, create_order, OrderStatus, save_image, get_list_of_admin_users, update_order_status, get_order_by_telegram_id, get_amount_of_pictures_in_order
from .database import ImageType
from aiohttp import ClientSession
import os
import re
import logging
import sqlalchemy as sa

TOKEN: str = os.environ.get("TOKEN")
order_creation_lock = Lock()

router = Router()

ADMIN_USERS = set()


async def load_admin_users():
    global ADMIN_USERS
    ADMIN_USERS = await get_list_of_admin_users()


async def get_photo(file_id: str, bot: Bot) -> bytes:
    async with ClientSession() as session:
        file = await bot.get_file(file_id)
        file_path = file.file_path
        download_url = f'https://api.telegram.org/file/bot{TOKEN}/{file_path}'

        async with session.get(download_url) as response:
            if response.status == 200:
                return await response.read()
            logging.error('Error downloading')
            raise FileNotFoundError()


def is_email(email: str) -> bool:
    """Verifies if string is an email"""

    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    if re.match(pattern, email):
        return True
    else:
        return False


@router.message(CommandStart())
async def cmd_start(message: Message):
    # TODO:
    # нужно сделать хорошее описание и добавить примеров фотографий
    welcome_message = (
        "🌟 Добро пожаловать в @ProfessionalPortraitBot, вашего помощника в создании деловых портретов! 🌟\n"
        "С ProfessionalPortraitBot вы можете легко преобразовать свои фотографии в профессиональные деловые портреты.)\n" 
        "Всё, что вам нужно, это:\n" 
        "- загрузить своё фото\n"
        "- оплатить услугу\n"
        "- дождаться готовности и получить свои портреты\n"
        "Повысьте свой профессиональный имидж с ProfessionalPortraitBot уже сегодня!\n"
    )
    await message.answer(welcome_message, reply_markup=kb.main)


class CreateOrderForPortrait(StatesGroup):
    order_id = State()
    email = State()
    photo_count = State()


@router.message(F.text == "Заказать портрет")
async def order_portrait(message: Message, state: FSMContext):
    if not await user_registered(message.from_user.id):
        await state.set_state(CreateOrderForPortrait.email)
        await state.update_data(photo_count=0)
        await message.answer("Вы у нас первый раз. Для продолжения авторизуйтесь", reply_markup=ReplyKeyboardRemove())
        await message.answer("Введите ваш контактный email")
    else:
        await state.set_state(CreateOrderForPortrait.photo_count)
        await message.answer(
            text="Загрузите минимум 11 фотографий с вашим изображением через добавление фото.\nЧем лучше исходные фотографии тем лучше качество",
            reply_markup=ReplyKeyboardRemove()
            )


@router.message(CreateOrderForPortrait.email)
async def order_input_email(message: Message, state: FSMContext):
    if not is_email(message.text):
        await message.answer("Для продолжения введите корректный имейл.")
    else:
        await create_user(telegram_id=message.from_user.id, telegram_name=message.from_user.username, email=message.text)
        await state.set_state(CreateOrderForPortrait.photo_count)
        await message.answer("Загрузите минимум 11 фотографий с вашим изображением через добавление фото.\n\nЧем лучше исходные фотографии тем лучше качество")


@router.message(CreateOrderForPortrait.photo_count)
async def order_input_photo_count(message: Message, bot: Bot, state: FSMContext):
    async with order_creation_lock:
        data = await state.get_data()
        try:
            order = await get_order_by_telegram_id(telegram_id=message.from_user.id)
        except sa.exc.MultipleResultsFound():
            raise ValueError("Collision with orders. Can not exist two orders with the same status PREPARATION")
        if order is None:
            order = await create_order(
                telegram_id=message.from_user.id,
                order_status=OrderStatus.PREPARATION,
                )
            await state.update_data(order_id=order.id)
            await state.set_state(CreateOrderForPortrait.photo_count)

        file_id = message.photo[-1].file_id
        image_binary = await get_photo(file_id=file_id, bot=bot)
        counter = data.get("photo_count", 0)
        await save_image(order_id=order.id, image_binary=image_binary, image_type=ImageType.RAW)
        counter += 1
        await state.update_data(photo_count=counter)

        if counter < 3:
            await message.answer(f"Загружена {counter} из минимума 11 фотографий. Продолжайте загружать")
        else:
            await state.update_data(order_id=order.id, photo_count=counter)
            await state.set_state(CreateOrderForPortrait.photo_count)
            await message.answer(f"Вы загрузили {counter} фотографии.")
            await message.answer("Этого достаточно для начала обработки")
            await message.answer("Вы можете продолжить загружать еще для лучшего результата.")
            await message.answer( f"\nПо окончанию нажмите кнопку 'Завершить загрузку'", reply_markup=await kb.finish_upload_kb())


@router.callback_query(CreateOrderForPortrait.photo_count)
async def order_input_photo_finish(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if callback.data == "finish_upload":
        await state.clear()
        await update_order_status(order_id=data.get('order_id'), order_status=OrderStatus.PAYMENT_APPROVAL_REQUIRED)
        await callback.message.answer("Загрузка окончена.")
        await callback.message.answer(f"Создана заявка №{data.get('order_id')}.")
        await callback.message.answer(
            f"\nПроизведите оплату через СБП в размере 5000 рублей по номеру +79116075951."
            f"\nКак только оплата будет подтверждена ваша заявка будет подана на обработку и вы получите оповещение."
        )


@router.message(F.text == "/start")
async def order_portrait(message: Message):
    if not await user_registered(message.from_user.id):
        await message.answer("Введите ваш контактный email")
    else:
        await message.answer("Загрузите 11 фотографий с вашим изображением через добавление фото.")


@router.message(Command('admin'))
async def admin_command(message: Message, bot: Bot):
    await load_admin_users()

    if message.from_user.id not in ADMIN_USERS:
        await message.answer("У вас нет прав для использования этой команды.")
    else:
        await bot.send_message(
            chat_id=message.chat.id,
            text="Панель Адимнистратора",
            reply_markup=ReplyKeyboardRemove()
            )
        await bot.send_message(
            chat_id=message.chat.id,
            text="Выберите опции",
            reply_markup=await kb.admin_inline_kb()
            )


@router.callback_query(F.data == "return")
async def admin_command(callback: CallbackQuery):
    await cmd_start(callback.message)


class ChangeOrderState(StatesGroup):
    order_id = State()
    state = State()


@router.callback_query(F.data == "change_status")
async def admin_command(callback: CallbackQuery, state: FSMContext):
    await callback.answer("")
    await load_admin_users()
    if callback.from_user.id not in ADMIN_USERS:
        await callback.message.answer("У вас нет прав для использования этой команды.")
    else:
        await callback.message.answer("Изменение статуса заказа")
        await state.set_state(ChangeOrderState.order_id)
        try:
            await callback.message.answer("Выберите номер заказа", reply_markup=await kb.order_list_inline_kb(operation_type=callback.data))
        except ValueError as e:
            await callback.message.answer("Нет ордеров для обработки")
            await state.clear()


@router.callback_query(ChangeOrderState.order_id)
async def admin_change_state_step_2(callback: CallbackQuery, state: FSMContext):
    await state.update_data(order_id=callback.message.text)
    await state.set_state(ChangeOrderState.state)
    await callback.message.answer("Выберите новый статус", reply_markup=await kb.status_list_inline_kb())


@router.callback_query(ChangeOrderState.state)
async def admin_change_state_step_3(callback: CallbackQuery, state: FSMContext):
    if callback.data != "return":
        await state.update_data(state=callback.message.text)
        data = await state.get_data()
        await callback.message.answer(f'Заказ  №{data.get("order_id")} переведен в статус {data.get("state")}')
        await state.clear()
    else:
        await callback.message.answer("Выберите новый статус", reply_markup=await kb.status_list_inline_kb())
    await state.clear()


class UploadProcessedPhotos(StatesGroup):
    order_id = State()
    photo_count = State()


@router.callback_query(F.data == "upload_photo")
async def admin_upload_photos_step_1(callback: CallbackQuery, state: FSMContext):
    await callback.answer("")
    await load_admin_users()
    if callback.from_user.id not in ADMIN_USERS:
        await callback.message.answer("У вас нет прав для использования этой команды.")
    else:
        await state.set_state(UploadProcessedPhotos.order_id)
        try:
            await callback.message.answer("Выберите номер заказа к которому будет загружены обработанные фото", reply_markup=await kb.order_list_inline_kb(operation_type=callback.data))
        except ValueError as e:
            await callback.message.answer("Нет ордеров для обработки")
            await state.clear()


@router.callback_query(UploadProcessedPhotos.order_id)
async def admin_upload_photos_step_2(callback: CallbackQuery, state: FSMContext):
    await state.update_data(order_id=callback.data.split("_")[1])
    await state.update_data(photo_count=0)
    await state.set_state(UploadProcessedPhotos.photo_count)
    await callback.message.answer("Должно быть загружено 20 фотографий. Загрузите фото.")


@router.message(UploadProcessedPhotos.photo_count)
async def admin_upload_photos_step_3(message: Message, bot: Bot, state: FSMContext):
    data = await state.get_data()
    file_id = message.photo[-1].file_id
    counter = int(data["photo_count"])
    if counter < 20:
        image_binary = await get_photo(file_id=file_id, bot=bot)
        await save_image(order_id=data.get('order_id'), image_binary=image_binary, image_type=ImageType.PROCESSED)
        counter += 1
        await state.update_data(photo_count=counter)
        await state.set_state(UploadProcessedPhotos.photo_count)
        await message.answer(f"Загружена {counter} из 20 фотографий. Продолжайте загружать")
    else:
        await state.clear()  # Clear the state to conclude the image upload process
        await message.answer("Процесс загрузки фото завершен.")
