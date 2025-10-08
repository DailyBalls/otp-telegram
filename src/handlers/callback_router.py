from aiogram import Router
from aiogram import F 
from aiogram.filters import Filter, MagicData
from aiogram.types import Message
from aiogram.types.callback_query import CallbackQuery

from handlers.callbacks.callback_login import callback_login
from handlers.callbacks.callback_register import callback_register_init, callback_register_bank, callback_register_edit, callback_register_cancel, callback_register_confirm_yes, callback_register_confirm_no
from handlers.middlewares.register_session import RegisterSessionMiddleware

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
callback_router.callback_query.register(callback_register_init, Text(data="register"))

# callback_router.callback_query.register(callback_login, Text(data="login"))
register_router = Router()
register_router.callback_query.middleware(RegisterSessionMiddleware())
register_router.callback_query.register(callback_register_cancel, Text(data="register_cancel"))
register_router.callback_query.register(callback_register_edit, TextPrefix(prefix="register_edit_"))
register_router.callback_query.register(callback_register_bank, TextPrefix(prefix="register_bank_"))
register_router.callback_query.register(callback_register_confirm_yes, Text(data="register_confirm_yes"))
register_router.callback_query.register(callback_register_cancel, Text(data="register_confirm_no"))
callback_router.include_router(register_router)