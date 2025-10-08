from typing import Optional
from pydantic import BaseModel
from aiogram import types
from aiogram.fsm.context import FSMContext
from bot_instance import bot
from contextlib import suppress
import asyncio
from .base_state_model import BaseStateModel

class ModelRegister(BaseStateModel):
    username: Optional[str] = None
    phone_number: Optional[str] = None
    password: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    list_messages_ids: Optional[list[int]] = None
    chat_id: Optional[int] = None
    bank_list: Optional[list[str]] = None
    is_required_captcha: Optional[bool] = False
    fill_captcha: Optional[str] = None

    def _get_state_key(self) -> str:
        """Override to use 'register' as the state key"""
        return "register"

    def set_username(self, value: str):
        self.username = value
        self._auto_save_if_enabled()

    def set_phone_number(self, value: str):
        self.phone_number = value
        self._auto_save_if_enabled()

    def set_password(self, value: str):
        self.password = value
        self._auto_save_if_enabled()

    def set_bank_name(self, value: str):
        self.bank_name = value
        self._auto_save_if_enabled()

    def set_bank_account_name(self, value: str):
        self.bank_account_name = value
        self._auto_save_if_enabled()

    def set_bank_account_number(self, value: str):
        self.bank_account_number = value
        self._auto_save_if_enabled()

    def set_chat_id(self, value: int):
        self.chat_id = value
        self._auto_save_if_enabled()

    def set_bank_list(self, value: list):
        self.bank_list = value
        self._auto_save_if_enabled()

    def set_is_required_captcha(self, value: bool):
        self.is_required_captcha = value
        self._auto_save_if_enabled()

    def set_fill_captcha(self, value: str):
        self.fill_captcha = value
        self._auto_save_if_enabled()

    def add_message_id(self, message_id: int) -> None:
        if self.list_messages_ids is None:
            self.list_messages_ids = []
        self.list_messages_ids.append(message_id)
        self._auto_save_if_enabled()

    async def delete_all_messages(self) -> None:
        if self.list_messages_ids is not None:
            with suppress(Exception):
                await bot.delete_messages(self.chat_id, self.list_messages_ids)

    def get_submit_registration_data(self) -> dict:
        return {
            "username": self.username,
            "telpon": self.phone_number,
            "rekening": self.bank_account_number,
            "password": self.password,
            "nama": self.bank_account_name,
            "bank": self.bank_name,
            "captcha": self.fill_captcha,
        }
                