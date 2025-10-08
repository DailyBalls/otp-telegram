from typing import Any, Dict, Type, Optional
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from .base_state_model import BaseStateModel


async def load_model_from_state(
    model_class: Type[BaseStateModel],
    fsm_context: FSMContext,
    event: Message | CallbackQuery,
    data: Dict[str, Any],
    data_key: str
) -> Optional[BaseStateModel]:
    """
    Helper function to load a model from FSM state with auto-save enabled.
    
    Args:
        model_class: The model class to instantiate (e.g., ModelUser, ModelRegister)
        fsm_context: The FSM context
        event: The Telegram event (Message or CallbackQuery)
        data: The handler data dictionary
        data_key: The key to store the model in the data dictionary
    
    Returns:
        The loaded model instance or None if not found
    """
    # Get FSM data
    fsm_data = await fsm_context.get_data()
    
    # Create temporary instance to get state key
    temp_model = model_class()
    state_key = temp_model._get_state_key()
    
    # Get model data from FSM
    model_data = fsm_data.get(state_key, False)
    
    if model_data:
        # Create model instance from JSON data
        model_instance = model_class.model_validate_json(model_data)
        model_instance._state = fsm_context
        model_instance._auto_save = True
        
        # Add message ID if applicable
        if isinstance(event, CallbackQuery):
            model_instance.add_message_id(event.message.message_id)
        elif isinstance(event, Message):
            model_instance.add_message_id(event.message_id)
        
        # Store in handler data
        data[data_key] = model_instance
        return model_instance
    
    return None


async def clear_model_from_state(
    model_class: Type[BaseStateModel],
    fsm_context: FSMContext
) -> None:
    """
    Helper function to clear a model from FSM state.
    
    Args:
        model_class: The model class to clear
        fsm_context: The FSM context
    """
    # Create temporary instance to get state key
    temp_model = model_class()
    state_key = temp_model._get_state_key()
    
    # Clear the state
    await fsm_context.update_data(**{state_key: None})
