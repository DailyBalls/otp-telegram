from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.types.inline_keyboard_button import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import BotConfig

async def cmd_start(msg: types.Message, config: BotConfig, state: FSMContext) -> None:
    """Process the `start` command"""

    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Login", callback_data="login"))
    builder.add(InlineKeyboardButton(text="Register", callback_data="register"))
    builder.adjust(2)  # One button per row
    await msg.answer(f"""
Halo <b>{msg.from_user.first_name}</b>!
Selamat datang di <b>{config.server_name}</b>!
Silahkan melakukan login atau register terlebih dahulu
""", reply_markup=builder.as_markup())

