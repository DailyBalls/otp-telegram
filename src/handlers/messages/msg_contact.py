from aiogram import Router, types
from aiogram.types.contact import Contact
from aiogram.fsm.context import FSMContext
from aiogram.types.keyboard_button import KeyboardButton
from aiogram.types.reply_keyboard_remove import ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from bot_instance import bot
from config import BotConfig
from handlers.commands.cmd_action import cmd_start_unauthenticated
from models.model_telegram_data import ModelTelegramData
from handlers.multi.multi_authentication import get_guest_menu_builder
async def msg_contact(msg: types.Message, config: BotConfig, state: FSMContext, telegram_data: ModelTelegramData) -> None:
    # Send confirmation message
    await msg.answer(
f"""✅ <b>Contact Verified Successfully!</b>
Terima kasih{", " + telegram_data.contact_name if telegram_data.contact_name else ""}!

Mohon tunggu, kami sedang mengambil informasi dari server kami.""", reply_markup=get_guest_menu_builder().as_markup(resize_keyboard=True))
    await bot.delete_message(msg.chat.id, msg.message_id)
    await cmd_start_unauthenticated(msg, config, state)




