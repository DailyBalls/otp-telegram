from typing import Type
from models.base_state_model import BaseStateModel
from aiogram.fsm.context import FSMContext

async def load_model(model_class: Type[BaseStateModel], state: FSMContext) -> BaseStateModel | None:
    # Get FSM data
    fsm_data = await state.get_data()
    
    # Create temporary instance to get state key
    temp_model = model_class()
    state_key = temp_model._get_state_key()
    
    # Get model data from FSM
    model_data = fsm_data.get(state_key, False)
    if model_data:
        model_instance = model_class.model_validate_json(model_data)
        model_instance._state = state
        return model_instance
    return None