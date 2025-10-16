from aiogram import Router, types
from aiogram.types.contact import Contact
from aiogram.fsm.context import FSMContext
from aiogram.types.keyboard_button import KeyboardButton
from aiogram.types.reply_keyboard_remove import ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from bot_instance import bot
from config import BotConfig
from handlers.commands.cmd_action import cmd_start_unauthenticated

async def msg_contact(msg: types.Message, config: BotConfig, state: FSMContext) -> None:
    
    contact = msg.contact
    username = msg.from_user.username

    if contact is None:
        await msg.answer("Please send a contact")
        return
    
    # Get the stored contact data from FSM (set by middleware)
    fsm_data = await state.get_data()
    stored_phone = fsm_data.get("contact_phone", contact.phone_number)
    stored_name = fsm_data.get("contact_name", contact.first_name)
    
    # markup = ReplyKeyboardRemove(remove_keyboard=True)
    
    # Send confirmation message
    await msg.answer(
f"""✅ <b>Contact Verified Successfully!</b>
Terima kasih{", " + username if username else ""}!

Mohon tunggu, kami sedang mengambil informasi dari server kami.""")
    await bot.delete_message(msg.chat.id, msg.message_id)
    await cmd_start_unauthenticated(msg, config, state)




