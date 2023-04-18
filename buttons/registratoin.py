from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

reg_agrees = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton("Да", callback_data="regUser_yes"),
        InlineKeyboardButton("Нет", callback_data="regUser_no")
    ]
])
