import asyncio
from typing import Optional
from aiogram.fsm.context import FSMContext
from pydantic import BaseModel
from aiogram import types
from bot_instance import bot
from contextlib import suppress
from .base_state_model import BaseStateModel

class ModelUser(BaseStateModel):
    username: Optional[str] = None
    balance: Optional[int] = None
    rank: Optional[str] = None
    list_messages_ids: Optional[list[int]] = None
    is_authenticated: Optional[bool] = False
    chat_id: Optional[int] = None

    def _get_state_key(self) -> str:
        """Override to use 'user' as the state key"""
        return "user"

    def add_message_id(self, message_id: int) -> None:
        if self.list_messages_ids is None:
            self.list_messages_ids = []
        self.list_messages_ids.append(message_id)
        self._auto_save_if_enabled()

    def set_username(self, value: str):
        self.username = value
        self._auto_save_if_enabled()

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
        await self.save_to_state()