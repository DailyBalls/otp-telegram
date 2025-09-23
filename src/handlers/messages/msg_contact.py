from aiogram import Router, types
from aiogram.types.contact import Contact

from config import BotConfig

async def msg_contact(msg: types.Message, config: BotConfig) -> None:
    
    contact = msg.contact
    user_id = msg.from_user.id
    username = msg.from_user.username

    if contact is None:
        await msg.answer("Please send a contact")
        return
    
    
    await msg.answer(
f"""Terima kasih{", " + username if username else ""}! 
Kami memiliki informasi kontak Anda 
(+{contact.phone_number}). 

Mohon tunggu, kami sedang mengambil informasi akun Anda dari server kami.""")

