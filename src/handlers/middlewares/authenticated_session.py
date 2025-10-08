from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from models.model_user import ModelUser


class AuthenticatedSessionMiddleware(BaseMiddleware):
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
        
        # Get current FSM data
        fsm_data = await fsm_context.get_data()
        
        # Check if user has already verified their contact
        user_model = ModelUser()
        state_key = user_model._get_state_key()
        user_data = fsm_data.get(state_key, False)
        
        if user_data:
            user_model = ModelUser.model_validate_json(user_data)
            user_model._state = fsm_context
            user_model._auto_save = True
            if isinstance(event, CallbackQuery):
                user_model.add_message_id(event.message.message_id)
            elif isinstance(event, Message):
                user_model.add_message_id(event.message_id)
            data['user_model'] = user_model
            # User has already verified contact, allow request to continue
            return await handler(event, data)
        
        await event.answer("Sesi telah berakhir, silahkan login kembali")
        await fsm_context.update_data(**{state_key: None})
        return  # Block the handler from executing
        