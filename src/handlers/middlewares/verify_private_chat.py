from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.enums.chat_type import ChatType
from aiogram.types import Message, chat

class VerifyPrivateChatMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        pass

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        if event.chat.type in (
            ChatType.GROUP,
            ChatType.SUPERGROUP,
            ChatType.CHANNEL,
        ):
            await event.answer("Silahkan gunakan bot ini di private chat")
            return
        return await handler(event, data)