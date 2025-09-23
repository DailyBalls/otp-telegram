from aiogram import Router, types
from aiogram.types.keyboard_button import KeyboardButton
from aiogram.types.reply_keyboard_markup import ReplyKeyboardMarkup 
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from config import BotConfig

async def cmd_start(msg: types.Message, config: BotConfig) -> None:
    """Process the `start` command"""
    await msg.answer(
        f"""Welcome to <b>{config.server_name}</b>!

        """)

    markup = ReplyKeyboardBuilder()
    b5 = KeyboardButton(text="Share a number",request_contact=True)
    markup.add(b5)

    await msg.answer("To Enjoy our game, please login by using phone number", reply_markup=markup.as_markup(resize_keyboard=True, one_time_keyboard=True))
