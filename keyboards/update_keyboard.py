from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

"""

"""

button_1 = InlineKeyboardButton(text="Хреначь!", callback_data="update_answer yes")
button_2 = InlineKeyboardButton(text="Напугал, ненадо", callback_data="update_answer no")
update_keyboard = InlineKeyboardMarkup(row_width=2).add(button_1, button_2)