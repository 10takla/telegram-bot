from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


change = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton("Изменить", callback_data="changeMe_"),
    ]
])

