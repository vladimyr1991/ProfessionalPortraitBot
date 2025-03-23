from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup


def main_menu_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🆓 Free Prompting", callback_data="free_prompting")],
            [InlineKeyboardButton(text="✨ Generate with My Photos", callback_data="model_free_prompting")],
            ]
        )
