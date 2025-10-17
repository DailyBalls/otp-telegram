from typing import Optional

from .base_state_model import BaseStateModel


class ModelTelegramData(BaseStateModel):
    contact_verified: Optional[bool] = False
    contact_phone: Optional[str] = None
    contact_name: Optional[str] = None
    user_id: Optional[int] = None
    list_messages_ids: Optional[list[int]] = None
    
    def _get_state_key(self) -> str:
        return "telegram_data"

    def add_message_id(self, message_id: int) -> None:
        if self.list_messages_ids is None:
            self.list_messages_ids = []
        self.list_messages_ids.append(message_id)
        self._auto_save_if_enabled()