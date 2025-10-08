from atexit import register
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, KeyboardButton, Message
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from config import BotConfig
from handlers.middlewares.base_model_middleware import BaseModelMiddleware
from models.model_register import ModelRegister


class RegisterSessionMiddleware(BaseModelMiddleware):
    def __init__(self) -> None:
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        self.fsm_context = data['state']
        self.data = data
        
        register_model = await self.load_model(ModelRegister, 'register_model')
        if not register_model:
            await event.answer("Silahkan ulangi proses register")
            return  # Block the handler from executing
                
        if isinstance(event, CallbackQuery):
            register_model.add_message_id(event.message.message_id)
        elif isinstance(event, Message):
            register_model.add_message_id(event.message_id)

        # User has already verified contact, allow request to continue
        return await handler(event, data)
