import asyncio
from datetime import datetime
from typing import Optional, Required

from bot_instance import bot

from models.base_state_model import BaseStateModel

class ModelAction(BaseStateModel):
    current_action: Optional[str] = None
    action_data: Optional[dict] = {}
    action_started_at: Optional[datetime] = datetime.now()
    chat_id: Optional[int] = None
    list_messages_ids: Optional[list[int]] = None

    def _get_state_key(self) -> str:
        return "action"
    
    def add_message_id(self, message_id: int) -> None:
        if self.list_messages_ids is None:
            self.list_messages_ids = []
        self.list_messages_ids.append(message_id)
        self._auto_save_if_enabled()

    def unset_message_id(self, message_id: int) -> None:
        if self.list_messages_ids is not None:
            self.list_messages_ids.remove(message_id)
            self._auto_save_if_enabled()
    
    async def delete_all_messages(self) -> None:
        if self.list_messages_ids is not None and self.chat_id is not None:
            # print("Deleting messages", self.list_messages_ids)
            await bot.delete_messages(self.chat_id, self.list_messages_ids)
        self.list_messages_ids = None
        self.chat_id = None
        self._auto_save_if_enabled()

    async def finish_action(self) -> None:
        await self.delete_all_messages()
        self.current_action = None
        self.action_data = None
        self.action_started_at = None
        self.chat_id = None
        await self.save_to_state()

    def set_action_data(self, key: str, value: any) -> None:
        if self.action_data is None:
            self.action_data = {}
        self.action_data[key] = value
        self._auto_save_if_enabled()

    def get_action_data(self, key: str) -> any:
        if self.action_data is None:
            return None
        return self.action_data.get(key)