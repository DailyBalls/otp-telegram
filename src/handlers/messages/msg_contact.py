from aiogram import Router, types
from aiogram.types.contact import Contact
from aiogram.fsm.context import FSMContext

from config import BotConfig

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
    
    # Send confirmation message
    await msg.answer(
f"""✅ <b>Contact Verified Successfully!</b>
Terima kasih{", " + username if username else ""}!
📱 Phone: +{stored_phone}
👤 Name: {stored_name}

Mohon tunggu, kami sedang mengambil informasi akun Anda dari server kami.""")



