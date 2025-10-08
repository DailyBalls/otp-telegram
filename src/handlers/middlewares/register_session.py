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
        fsm_context: FSMContext = data['state']
        
        if fsm_context is None:
            # FSM context not available, allow request to continue
            # This can happen if middleware is applied to routers without FSM
            return await handler(event, data)
        
        # Get current FSM data
        fsm_data = await fsm_context.get_data()
        
        # Check if user has already verified their contact
        register_data = fsm_data.get("register", False)
        
        if register_data:
            register_model = ModelRegister.model_validate_json(register_data)
            register_model._state = fsm_context
            register_model._auto_save = True
            if isinstance(event, CallbackQuery):
                register_model.add_message_id(event.message.message_id)
            elif isinstance(event, Message):
                register_model.add_message_id(event.message_id)
            data['register_model'] = register_model
            # User has already verified contact, allow request to continue
            return await handler(event, data)
        
        await event.answer("Silahkan ulangi proses registrasi dari awal")
        await fsm_context.update_data(register=None)
        return  # Block the handler from executing
        