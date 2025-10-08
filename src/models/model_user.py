from typing import Optional
from pydantic import BaseModel
from aiogram import types
from bot_instance import bot
from contextlib import suppress

class ModelUser(BaseModel):
    username: Optional[str] = None
    list_messages_ids: Optional[list[int]] = None
    chat_id: Optional[int] = None
    is_authenticated: Optional[bool] = False

    def add_message_id(self, message_id: int) -> None:
        if self.list_messages_ids is None:
            self.list_messages_ids = []
        self.list_messages_ids.append(message_id)

    async def delete_all_messages(self) -> None:
        if self.list_messages_ids is not None:
            with suppress(Exception):
                await bot.delete_messages(self.chat_id, self.list_messages_ids)

    async def logout(self) -> None:
        await self.delete_all_messages()
        self.username = None
        self.is_authenticated = False
        self.list_messages_ids = None
        self.chat_id = None
        await self.save()