from typing import Any, Awaitable, Callable, Dict, Type
from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from models.base_state_model import BaseStateModel
import utils.models as model_utils


class BaseModelMiddleware(BaseMiddleware):
    """Base middleware class with load_model functionality"""
    
    def __init__(self):
        self.fsm_context = None
        self.data = None
    
    async def load_model(
        self,
        model_class: Type[BaseStateModel],
        data_key: str | None = None
    ) -> BaseStateModel | None:
        """Load model from FSM state with auto-save enabled"""
        # Get FSM data
        model_data = await model_utils.load_model(model_class, self.fsm_context, data_key)
        
        if model_data:
            # Store in handler data
            if data_key:
                self.data[data_key] = model_data
            return model_data
        
        return None
