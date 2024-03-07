from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from .database import OrderStatus
from .database import get_list_of_orders_for_admin

main = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Заказать портрет")]
    ])


async def make_order_inline_kb():
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(
            text="Сгенерировать потрет",
            callback_data="create_order"
            )
        )

    return keyboard.as_markup()


async def admin_inline_kb():
    button_1 = InlineKeyboardButton(text="Изменить статус заказа", callback_data='change_status')
    button_2 = InlineKeyboardButton(text="Загрузить обработанные фото", callback_data="upload_photo")
    button_3 = InlineKeyboardButton(text="Назад", callback_data="return")

    inline_keyboard = [[button_1], [button_2], [button_3]]

    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


async def order_list_inline_kb(operation_type):
    keyboard = InlineKeyboardBuilder()
    orders_id = await get_list_of_orders_for_admin(operation_type)
    if len(orders_id) == 0:
        raise ValueError("No orders")
    for order_id in orders_id:
        keyboard.add(
            InlineKeyboardButton(text=f"Заказ: №{str(order_id)}", callback_data=f'{order_id}')
            )
    keyboard.add(
        InlineKeyboardButton(text="Назад", callback_data="return")
        )
    return keyboard.as_markup()


async def status_list_inline_kb():
    inline_keyboard = [[InlineKeyboardButton(text=status.value, callback_data=f'{status.name}')] for status in
            [OrderStatus.PAYMENT_APPROVED, OrderStatus.PROCESSED_IMAGES_UPLOADED]]
    inline_keyboard.append([InlineKeyboardButton(text="Назад", callback_data="return")])

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=inline_keyboard
        )
    return keyboard


async def finish_upload_kb():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Завершить загрузку", callback_data="finish_upload")]
            ]
        )
    return keyboard
