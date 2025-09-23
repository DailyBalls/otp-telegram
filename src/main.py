import asyncio
from os import getenv
from aiogram.fsm.storage.redis import RedisStorage
from dotenv import load_dotenv

from handlers.command_router import command_router
from handlers.message_handler import message_router
load_dotenv()

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.middleware import FSMContextMiddleware

from bot_instance import bot, States
from config import BotConfig
import redis.asyncio as redis



TOKEN = getenv("BOT_TOKEN")
WHITELIST_MODE = str(getenv("WHITELIST_MODE")).lower() == "true"
SERVER_NAME = getenv("SERVER_NAME")
WHITELIST_IDS = [ 
    
]


def register_routers(dp: Dispatcher) -> None:
    """Registers routers"""
    dp.include_router(command_router)
    dp.include_router(message_router)


async def main() -> None:
    """The main function which will execute our event loop and start polling."""
    redis_client = redis.Redis(host=getenv("REDIS_HOST"), port=getenv("REDIS_PORT"), password=getenv("REDIS_PASSWORD"), socket_connect_timeout=3)
    await redis_client.ping()
    print("Redis connected")
    redis_storage = RedisStorage(redis=redis_client)
    
    config = BotConfig(server_name=SERVER_NAME, whitelist_mode=WHITELIST_MODE, whitelist_ids=WHITELIST_IDS)

    dp = Dispatcher(storage=redis_storage)
    dp["config"] = config

    register_routers(dp)
    
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())