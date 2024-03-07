import logging
import os
import re
from asyncio import Lock

import sqlalchemy as sa
from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery
from aiogram.types import ReplyKeyboardRemove
from aiohttp import ClientSession

from . import keyboards as kb
from .database import ImageType
from .database import create_user, user_registered, create_order, OrderStatus, save_image, get_list_of_admin_users, update_order_status, get_order_by_telegram_id, OrderStatus

TOKEN: str = os.environ.get("TOKEN")
order_creation_lock = Lock()

router = Router()


async def load_admin_users():
    admin_users = await get_list_of_admin_users()
    return admin_users


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
    welcome_message_1 = "🌟 Добро пожаловать в @ProfessionalPortraitBot, вашего помощника в создании деловых портретов! 🌟"
    welcome_message_2 = ("Вы можете легко преобразовать свои фотографии в профессиональные деловые портреты. "
                         "Не нужно тратить время на фотосессии. "
                         "Просто проследуйте простой инструкции и получите ваши фотографии уже сегодня.")

    await message.answer(welcome_message_1)
    await message.answer(text=welcome_message_2, reply_markup=await kb.make_order_inline_kb())


@router.message(Command('admin'))
async def admin_command(message: Message, bot: Bot):
    admin_users = await load_admin_users()

    if message.from_user.id not in admin_users:
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
    status = State()


@router.callback_query(F.data == "change_status")
async def admin_command(callback: CallbackQuery, state: FSMContext):
    await callback.answer("")
    admin_users = await load_admin_users()
    if callback.from_user.id not in admin_users:
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
    order_id = callback.data
    await state.update_data(order_id=order_id)
    await state.set_state(ChangeOrderState.status)
    await callback.message.answer("Выберите новый статус", reply_markup=await kb.status_list_inline_kb())


@router.callback_query(ChangeOrderState.status)
async def admin_change_state_step_3(callback: CallbackQuery, state: FSMContext):
    if callback.data != "return":
        data = await state.get_data()

        status: OrderStatus = OrderStatus[callback.data]
        order_id: int = data["order_id"]
        await update_order_status(
            order_id=order_id,
            order_status=status
            )
        await callback.message.answer(f'Заказ  №{order_id} переведен в статус {status.value}')
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
    admin_users = await load_admin_users()
    if callback.from_user.id not in admin_users:
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


class CreateOrderForPortrait(StatesGroup):
    order_id = State()
    photo_count = State()
    is_ready = State()


@router.callback_query(F.data == "create_order")
async def order_portrait(callback: CallbackQuery, state: FSMContext):
    if not await user_registered(callback.from_user.id):
        await create_user(
            telegram_id=callback.from_user.id,
            telegram_name=callback.from_user.username
            )
    await state.update_data(photo_count=0, upload_finished=False, is_ready=False)
    await state.set_state(CreateOrderForPortrait.photo_count)
    await callback.message.answer(
        text=("Загрузите минимум 11 фотографий с вашим изображением через добавление фото."
              "\nЧем лучше исходные фотографии тем лучше качество"),
        reply_markup=ReplyKeyboardRemove()
        )


@router.message(CreateOrderForPortrait.photo_count)
async def order_input_photo_count(message: Message, bot: Bot, state: FSMContext):
    async with order_creation_lock:
        await state.update_data(no_extra_data=False)
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
        image_binary = await get_photo(file_id=message.photo[-1].file_id, bot=bot)
        await save_image(order_id=order.id, image_binary=image_binary, image_type=ImageType.RAW)
        counter = data.get("photo_count", 0) + 1
        await state.update_data(photo_count=counter)

        if counter > 3 and not data.get("is_ready"):
            await state.update_data(is_ready=True)
            await state.set_state(CreateOrderForPortrait.order_id)
            await message.answer(f"Вы загрузили {counter} фотографии.")
            await message.answer("Этого достаточно для начала обработки")
            await message.answer("Вы можете продолжить загружать еще для лучшего результата.")
            await message.answer(
                text=f"По окончанию нажмите кнопку 'Завершить загрузку'",
                reply_markup=await kb.finish_upload_kb()
                )


@router.callback_query(CreateOrderForPortrait.order_id)
async def order_input_photo_finish(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if callback.data == "finish_upload":
        await update_order_status(order_id=data.get('order_id'), order_status=OrderStatus.PAYMENT_APPROVAL_REQUIRED)
        await state.clear()
        await callback.message.answer("Загрузка окончена.")
        await callback.message.answer(f"Создана заявка №{data.get('order_id')}.")
        await callback.message.answer(
            f"\nПроизведите оплату через СБП в размере 5000 рублей по номеру +79116075951."
            f"\nКак только оплата будет подтверждена ваша заявка будет подана на обработку и вы получите оповещение."
            )
