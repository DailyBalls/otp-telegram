from aiogram import Router, types
from aiogram.fsm.context import FSMContext

from config import BotConfig

async def cmd_unbind(msg: types.Message, state: FSMContext, config: BotConfig) -> None:
    """Process the `start` command"""
    await msg.answer("Unbinding...")

    contact_data = {
        "contact_verified": False,
        "contact_phone": None,
        "contact_name": None,
        "contact_user_id": msg.from_user.id
    }
    
    # Save contact data to FSM storage
    await state.update_data(**contact_data)
    await state.clear()

    await msg.answer("Unbinding successful")
