from contextlib import suppress

from bot_instance import bot
from .base_state_model import BaseStateModel
from typing import Optional

class ModelLogin(BaseStateModel):
    username: Optional[str] = None
    password: Optional[str] = None
    captcha: Optional[str] = None
    is_required_captcha: Optional[bool] = False
    list_messages_ids: Optional[list[int]] = None
    initiator_message_id: Optional[int] = None
    chat_id: Optional[int] = None
    
    def _get_state_key(self) -> str:
        return "login"
    
    def add_message_id(self, message_id: int) -> None:
        if self.list_messages_ids is None:
            self.list_messages_ids = []
        self.list_messages_ids.append(message_id)
        self._auto_save_if_enabled()
        
    async def delete_all_messages(self) -> None:
        if self.list_messages_ids is not None:
            with suppress(Exception):
                await bot.delete_messages(self.chat_id, self.list_messages_ids)

    def dump_data(self) -> dict:
        return {
            "username": self.username,
            "password": self.password,
            "captcha": self.captcha if self.captcha is not None else "",
        }