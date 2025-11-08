from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

def get_logged_in_menu_builder() -> ReplyKeyboardBuilder:
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="Menu"))
    builder.add(KeyboardButton(text="Deposit"))
    builder.add(KeyboardButton(text="Withdraw"))
    builder.add(KeyboardButton(text="Logout"))
    builder.adjust(2)
    return builder

def get_guest_menu_builder() -> ReplyKeyboardBuilder:
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="Login"))
    builder.add(KeyboardButton(text="Register"))
    builder.adjust(2)  # One button per row
    return builder