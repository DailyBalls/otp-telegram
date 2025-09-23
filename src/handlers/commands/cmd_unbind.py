from aiogram import Router, types
from aiogram.fsm.context import FSMContext

from config import BotConfig

async def cmd_unbind(msg: types.Message, state: FSMContext, config: BotConfig) -> None:
    """Process the `start` command"""
     # Check if FSM context is available
    
    if state is None:
        await msg.answer("Error: FSM context not available")
        return
    
    await msg.answer("Unbinding...")

    contact_data = {
        "contact_verified": False,
        "contact_phone": None,
        "contact_name": None,
        "contact_user_id": msg.from_user.id
    }
    
    # Save contact data to FSM storage
    await state.update_data(**contact_data)

    await msg.answer("Unbinding successful")
