from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


# Back button
def back_menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔙 Back to Main Menu")]
            ],
        resize_keyboard=True,
        one_time_keyboard=True
        )
