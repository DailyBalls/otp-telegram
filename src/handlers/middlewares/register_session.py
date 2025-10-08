from atexit import register
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, KeyboardButton, Message
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from config import BotConfig
from models.model_register import ModelRegister


class RegisterSessionMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        pass

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        # Check if FSM context is available
        fsm_state: FSMContext = data['state']
        
        # Get current FSM data
        fsm_data = await fsm_state.get_data()
        
        register_model = ModelRegister()
        register_model._state = fsm_state
        state_key = register_model._get_state_key()
        register_data = fsm_data.get(state_key, False)
        
        if register_data:
            register_model = ModelRegister.model_validate_json(register_data)
            if isinstance(event, CallbackQuery):
                register_model.add_message_id(event.message.message_id)
            elif isinstance(event, Message):
                register_model.add_message_id(event.message_id)
            data['register_model'] = register_model # Inject the register model into the data
            # User has already verified contact, allow request to continue
            return await handler(event, data)
        
        await event.answer("Silahkan ulangi proses registrasi dari awal")
        await register_model.delete_from_state()
        return  # Block the handler from executing
        