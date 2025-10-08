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
        fsm_state: FSMContext = data['state']
        
        # Get current FSM data
        fsm_data = await fsm_state.get_data()
        
        # Check if user has already verified their contact
        user_model = ModelUser()
        user_model._state = fsm_state
        state_key = user_model._get_state_key()
        user_data = fsm_data.get(state_key, False)
        
        if user_data:
            user_model = ModelUser.model_validate_json(user_data)
            if isinstance(event, CallbackQuery):
                user_model.add_message_id(event.message.message_id)
            elif isinstance(event, Message):
                user_model.add_message_id(event.message_id)
            data['user_model'] = user_model
            # User has already verified contact, allow request to continue
            return await handler(event, data)
        
        await event.answer("Sesi telah berakhir, silahkan login kembali")
        await user_model.delete_from_state()
        return  # Block the handler from executing
        