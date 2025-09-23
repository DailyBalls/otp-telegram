from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message

from config import BotConfig


class WhitelistedOnlyMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        pass

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        config: BotConfig = data["config"]
        if event.from_user.id not in config.whitelist_ids:
            await event.answer("You are not in the whitelist")
            return
        return await handler(event, data)