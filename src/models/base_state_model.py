from typing import Optional
from pydantic import BaseModel
from aiogram.fsm.context import FSMContext
import asyncio


class BaseStateModel(BaseModel):
    """Base model with state management functionality for FSM state management"""
    
    def __init__(self, state: FSMContext = None, auto_save: bool = True, **data):
        super().__init__(**data)
        self._state = state
        self._auto_save = auto_save
        self._save_task = None
        self._save_delay = 0.5  # 100ms debounce

    def _auto_save_if_enabled(self):
        """Trigger auto-save if enabled and state is available"""
        if self._auto_save and self._state:
            # Cancel previous save task if it exists
            if self._save_task and not self._save_task.done():
                # print("Cancelling previous save task")
                self._save_task.cancel()
            
            # Schedule new save with debounce
            self._save_task = asyncio.create_task(self._debounced_save())

    async def _debounced_save(self):
        """Debounced save to prevent rapid overwrites"""
        await asyncio.sleep(self._save_delay)
        await self._save_to_state()

    async def _save_to_state(self):
        """Save model data to FSM state"""
        if self._state:
            # print("Auto Saving model data to state", self._get_state_key())
            # Get the model name for the state key (e.g., 'register', 'user')
            state_key = self._get_state_key()
            await self._state.update_data(**{state_key: self.model_dump_json()})
            # print("Auto-saving model data to state", self._get_state_key())
            # Stev Code to Cancel the save task if it still exists
            if self._save_task and not self._save_task.done():
                self._save_task.cancel()
            # print(self.model_dump_json())

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

    async def delete_from_state(self):
        """Delete the model from the state"""
        if self._state:
            await self._state.update_data(**{self._get_state_key(): None})

    async def fill_from_dict(self, data: dict):
        """Fill the model from a dictionary"""
        for key, value in data.items():
            setattr(self, key, value)
        self._auto_save_if_enabled()
