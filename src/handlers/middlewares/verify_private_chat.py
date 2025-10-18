from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.enums.chat_type import ChatType
from aiogram.types import CallbackQuery, Message, chat

class VerifyPrivateChatMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        pass

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        type_chat = None
        if isinstance(event, CallbackQuery):
            type_chat = event.message.chat.type
        elif isinstance(event, Message):
            type_chat = event.chat.type

        if type_chat is None:
            await event.answer("Terjadi kesalahan, silahkan ulangi proses")
            print("Gagal Mendapatkan type chat")
            return

        if type_chat in (
            ChatType.GROUP,
            ChatType.SUPERGROUP,
            ChatType.CHANNEL,
        ):
            await event.answer("Silahkan gunakan bot ini di private chat")
            return
        return await handler(event, data)