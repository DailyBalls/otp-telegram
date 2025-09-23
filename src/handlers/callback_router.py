from aiogram import Router
from aiogram import F 
from aiogram.filters import Filter, MagicData
from aiogram.types import Message
from aiogram.types.callback_query import CallbackQuery

from handlers.callbacks.callback_login import callback_login
from handlers.callbacks.callback_register import callback_register, callback_register_bank

class Text(Filter):
    def __init__(self, data: str) -> None:
        self.data = data

    async def __call__(self, callback: CallbackQuery) -> bool:
        return callback.data == self.data

class TextPrefix(Filter):
    def __init__(self, prefix: str) -> None:
        self.prefix = prefix

    async def __call__(self, callback: CallbackQuery) -> bool:
        return callback.data.startswith(self.prefix)

callback_router = Router()

# callback_router.callback_query.register(callback_login, Text(data="login"))
callback_router.callback_query.register(callback_register, Text(data="register"))
callback_router.callback_query.register(callback_register_bank, TextPrefix(prefix="register_bank_"))