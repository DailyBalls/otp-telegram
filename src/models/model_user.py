import asyncio
from typing import Optional
from aiogram.fsm.context import FSMContext
from pydantic import BaseModel
from aiogram import types
from bot_instance import bot
from contextlib import suppress

from models.model_deposit import DepositChannel
from .base_state_model import BaseStateModel


class RekeningAdd(BaseModel):
    list_active_banks: Optional[list[str]] = None
    bank_name: Optional[str] = None
    bank_account_name: Optional[str] = None
    bank_account_number: Optional[str] = None


class ModelUser(BaseStateModel):
    username: Optional[str] = None
    credit: Optional[str] = None
    rank: Optional[str] = None
    min_deposit: Optional[int] = None
    max_deposit: Optional[int] = None
    list_messages_ids: Optional[list[int]] = None
    is_authenticated: Optional[bool] = False
    chat_id: Optional[int] = None
    deposit_channels: Optional[list[DepositChannel]] = None
    temp_rekening_add: Optional[RekeningAdd] = None

    def _get_state_key(self) -> str:
        """Override to use 'user' as the state key"""
        return "user"

    def add_message_id(self, message_id: int) -> None:
        if self.list_messages_ids is None:
            self.list_messages_ids = []
        self.list_messages_ids.append(message_id)
        self._auto_save_if_enabled()
    
    def unset_message_id(self, message_id: int) -> None:
        if self.list_messages_ids is not None:
            self.list_messages_ids.remove(message_id)
            self._auto_save_if_enabled()

    def set_username(self, value: str):
        self.username = value
        self._auto_save_if_enabled()

    def set_credit(self, value: str):
        self.credit = value
        self._auto_save_if_enabled()
    
    def set_rank(self, value: str):
        self.rank = value
        self._auto_save_if_enabled()
    
    def set_deposit_amount(self, value: str):
        self.deposit_amount = value
        self._auto_save_if_enabled()

    async def delete_all_messages(self) -> None:
        if self.list_messages_ids is not None:
            with suppress(Exception):
                await bot.delete_messages(self.chat_id, self.list_messages_ids)

    async def logout(self) -> None:
        await self.delete_all_messages()
        await self.delete_from_state()

    def set_deposit_channels(self, data: list[DepositChannel]) -> None:
        self.deposit_channels = data
        self._auto_save_if_enabled()

    def get_deposit_channels_by_type(self, type: str) -> list[DepositChannel]:
        if self.deposit_channels is None:
            return []
        return [channel for channel in self.deposit_channels if channel.type == type]
