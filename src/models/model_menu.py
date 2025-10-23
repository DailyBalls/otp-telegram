from contextlib import suppress

from bot_instance import bot
from .base_state_model import BaseStateModel
from typing import Optional

class ModelMenu(BaseStateModel):
    list_menu_ids: Optional[list[int]] = None
    list_message_ids: Optional[list[int]] = None
    chat_id: Optional[int] = None
    logged_in: Optional[bool] = False

    def _get_state_key(self) -> str:
        return "menu"
    
    def add_menu_id(self, message_id: int) -> None:
        if self.list_menu_ids is None:
            self.list_menu_ids = []
        if self.list_message_ids is None:
            self.list_message_ids = []
        self.list_menu_ids.append(message_id)
        self.list_message_ids.append(message_id)
        self._auto_save_if_enabled()
        
    def add_message_id(self, message_id: int) -> None:
        if self.list_message_ids is None:
            self.list_message_ids = []
        self.list_message_ids.append(message_id)
        self._auto_save_if_enabled()
        
    async def delete_all_messages(self) -> None:
        if self.list_message_ids is not None:
            with suppress(Exception):
                await bot.delete_messages(self.chat_id, self.list_message_ids)

    async def delete_first_menu(self) -> None:
        if self.list_menu_ids is not None and len(self.list_menu_ids) > 0:
            with suppress(Exception):
                await bot.delete_message(self.chat_id, self.list_menu_ids[0])
            self.list_menu_ids.pop(0)
            self._auto_save_if_enabled()