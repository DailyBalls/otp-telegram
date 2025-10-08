# Example of how to create new auto-save models using the base class

from typing import Optional
from .base_auto_save_model import BaseAutoSaveModel

class ModelSettings(BaseAutoSaveModel):
    """Example model with auto-save functionality"""
    theme: Optional[str] = None
    language: Optional[str] = None
    notifications: Optional[bool] = True
    
    def _get_state_key(self) -> str:
        """Override to use 'settings' as the state key"""
        return "settings"
    
    def set_theme(self, value: str):
        self.theme = value
        self._auto_save_if_enabled()
    
    def set_language(self, value: str):
        self.language = value
        self._auto_save_if_enabled()
    
    def set_notifications(self, value: bool):
        self.notifications = value
        self._auto_save_if_enabled()

# Usage example:
# settings_model = ModelSettings(state=state)
# settings_model.set_theme("dark")  # Auto-saves to Redis!
# settings_model.set_language("en")  # Auto-saves to Redis!
