from typing import Optional

from .base_state_model import BaseStateModel

'''
Model to store telegram data
This model will be persistent even after logout
'''
class ModelTelegramData(BaseStateModel):
    contact_verified: Optional[bool] = False
    contact_phone: Optional[str] = None
    contact_name: Optional[str] = None
    user_id: Optional[int] = None
    list_messages_ids: Optional[list[int]] = None
    persistent_data: Optional[dict] = {}
    
    def _get_state_key(self) -> str:
        return "telegram_data"

    def add_message_id(self, message_id: int) -> None:
        if self.list_messages_ids is None:
            self.list_messages_ids = []
        self.list_messages_ids.append(message_id)
        self._auto_save_if_enabled()

    def set_persistent_data(self, key: str, value: any = None) -> None:
        if self.persistent_data is None:
            self.persistent_data = {}
        self.persistent_data[key] = value
        self._auto_save_if_enabled()    

    def get_persistent_data(self, key: str) -> any:
        if self.persistent_data is None:
            return None
        return self.persistent_data.get(key) or None