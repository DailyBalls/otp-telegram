from typing import Optional
from pydantic import BaseModel
from aiogram.fsm.context import FSMContext
import asyncio


class BaseAutoSaveModel(BaseModel):
    """Base model with auto-save functionality for FSM state management"""
    
    def __init__(self, state: FSMContext = None, auto_save: bool = True, **data):
        super().__init__(**data)
        self._state = state
        self._auto_save = auto_save

    def _auto_save_if_enabled(self):
        """Trigger auto-save if enabled and state is available"""
        if self._auto_save and self._state:
            asyncio.create_task(self._save_to_state())

    async def _save_to_state(self):
        """Save model data to FSM state"""
        if self._state:
            # Get the model name for the state key (e.g., 'register', 'user')
            state_key = self._get_state_key()
            await self._state.update_data(**{state_key: self.model_dump_json()})

    def _get_state_key(self) -> str:
        """Get the state key for this model. Override in subclasses if needed"""
        # Default: use lowercase class name
        return self.__class__.__name__.lower().replace('model', '')

    def enable_auto_save(self):
        """Enable auto-save functionality"""
        self._auto_save = True

    def disable_auto_save(self):
        """Disable auto-save functionality"""
        self._auto_save = False

    def set_state(self, state: FSMContext):
        """Set the FSM context for auto-save"""
        self._state = state

    async def save_to_state(self):
        """Manually save to state (bypasses auto-save flag)"""
        await self._save_to_state()
