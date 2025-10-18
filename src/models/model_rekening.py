from typing import Optional
from pydantic import BaseModel


class Rekening(BaseModel):
    bank_name: Optional[str] = None
    bank_account_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    default: Optional[bool] = False
    list_messages_ids: Optional[list[int]] = None

    def add_message_id(self, message_id: int) -> None:
        if self.list_messages_ids is None:
            self.list_messages_ids = []
        self.list_messages_ids.append(message_id)
        self._auto_save_if_enabled()