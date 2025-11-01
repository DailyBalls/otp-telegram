import asyncio
from datetime import datetime
from typing import Optional, Required
from aiogram.fsm.context import FSMContext
from pydantic import BaseModel
from aiogram import types
from bot_instance import bot
from contextlib import suppress

from models.model_deposit import DepositChannel
from .base_state_model import BaseStateModel

STATUS_SUSPEND = "2"
STATUS_ACTIVE = "1"
STATUS_INACTIVE = "0"

class RekeningAdd(BaseModel):
    initiator_message_id: Optional[int] = None
    list_active_banks: Optional[list[str]] = None
    list_user_banks: Optional[list[str]] = None
    bank_name: Optional[str] = None
    bank_account_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    list_messages_ids: Optional[list[int]] = None
    chat_id: Optional[int] = None

class UserAction(BaseModel):
    current_action: Optional[str] = None
    action_data: Optional[dict] = {}
    action_started_at: Optional[datetime] = datetime.now()
    chat_id: Optional[int] = None
    list_messages_ids: Optional[list[int]] = None
    list_menu_ids: Optional[list[int]] = None

    '''
    NOT FOR USE DIRECTLY, USE model_user.finish_action INSTEAD
    '''
    async def _finish(self) -> None:
        await self.delete_all_messages()
        self.current_action = None
        self.action_data = None
        self.action_started_at = None
        self.chat_id = None

    async def initiate(self, action: str, **kwargs) -> None:
        self.current_action = action
        self.action_data = kwargs
        self.action_started_at = datetime.now()
        self.chat_id = kwargs.get("chat_id")
        self._auto_save_if_enabled()
        return

    async def delete_all_messages(self) -> None:
        if self.list_messages_ids is not None and self.chat_id is not None:
            with suppress(Exception):
                await bot.delete_messages(self.chat_id, self.list_messages_ids)
        self.list_messages_ids = None
        self.chat_id = None

    def _add_menu_id(self, menu_id: int) -> None:
        if self.list_messages_ids is None:
            self.list_messages_ids = []
        self.list_messages_ids.append(menu_id)
        if self.list_menu_ids is None:
            self.list_menu_ids = []
        self.list_menu_ids.append(menu_id)

    def unset_menu_id(self, menu_id: int) -> None:
        if self.list_menu_ids is not None:
            self.list_menu_ids.remove(menu_id)

    def _add_message_id(self, message_id: int) -> None:
        if self.list_messages_ids is None:
            self.list_messages_ids = []
        self.list_messages_ids.append(message_id)
    
    def unset_message_id(self, message_id: int) -> None:
        if self.list_messages_ids is not None:
            self.list_messages_ids.remove(message_id)

    def set_action_data(self, key: str, value: any) -> None:
        if self.action_data is None:
            self.action_data = {}
        self.action_data[key] = value
    
    def get_action_data(self, key: str) -> any:
        if self.action_data is None:
            return None
        return self.action_data.get(key)



class ModelUser(BaseStateModel):
    username: Optional[str] = None
    name: Optional[str] = None
    credit: Optional[str] = None
    rank: Optional[str] = None
    min_deposit: Optional[int] = None
    max_deposit: Optional[int] = None
    list_messages_ids: Optional[list[int]] = None
    is_authenticated: Optional[bool] = False
    chat_id: Optional[int] = None
    deposit_channels: Optional[list[DepositChannel]] = None
    temp_rekening_add: Optional[RekeningAdd] = None
    action: Optional[UserAction] = None
    pending_wd: Optional[bool] = False
    pending_deposit: Optional[bool] = False
    status: Optional[str] = STATUS_ACTIVE
    show_rank: Optional[bool] = True
    
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

    def add_rekening_message_id(self, message_id: int) -> None:
        if self.temp_rekening_add is None: 
            raise Exception("Temp RekeningAdd model not initiated")

        self.temp_rekening_add.list_messages_ids.append(message_id)
        self.add_message_id(message_id)
        self._auto_save_if_enabled()
        return

    def initiate_action(self, action: str, **kwargs) -> None:
        self.action = UserAction(current_action=action, chat_id=self.chat_id, **kwargs)
        self._auto_save_if_enabled()
        return

    async def await_finish_action(self) -> None:
        await self.action._finish()
        self.action = None
        await self.save_to_state()

    def finish_action(self) -> None:
        asyncio.create_task(self.await_finish_action())
        return

    def add_action_message_id(self, message_id: int) -> None:
        if self.action is None:
            raise Exception("Action model not initiated")
        self.action._add_message_id(message_id)
        self.list_messages_ids.append(message_id)
        self._auto_save_if_enabled()

    def add_action_menu_id(self, menu_id: int) -> None:
        if self.action is None:
            raise Exception("Action model not initiated")
        self.action._add_menu_id(menu_id)
        self.action._add_message_id(menu_id)
        self.list_messages_ids.append(menu_id)
        self._auto_save_if_enabled()

    def is_active(self) -> bool:
        return self.status == STATUS_ACTIVE

    def get_status_text(self) -> str:
        return "Suspend" if self.status == STATUS_SUSPEND else "Nonaktif"
