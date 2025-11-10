from os import getenv, path
from typing import Literal
from aiogram.fsm.storage.base import DefaultKeyBuilder, StorageKey
from dotenv import load_dotenv


if getenv("ENV_FILE") is not None:
    ENV_FILE = getenv("ENV_FILE") or ".env"
    ENV_PATH = path.join(path.dirname(path.dirname(__file__)), ENV_FILE)
    load_dotenv(ENV_PATH)

import asyncio
from aiogram.fsm.storage.redis import RedisStorage

from handlers.command_router import command_router
from handlers.message_router import message_router
from handlers.callback_router import callback_router

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.middleware import FSMContextMiddleware

from bot_instance import bot
from config import BotConfig
import redis.asyncio as redis

from utils.logger import setup_logger


TOKEN = getenv("BOT_TOKEN")
WHITELIST_MODE = str(getenv("WHITELIST_MODE")).lower() == "true"
WEB_ID = getenv("WEB_ID")
SITE_NAME = getenv("SITE_NAME")
OTP_HOST = getenv("OTP_HOST")
WHITELIST_IDS = [ 
    7957553101
]

# Initialize logger
logger = setup_logger(web_id=WEB_ID)

config: BotConfig = None

class RedisKeyBuilder(DefaultKeyBuilder):
    def build(self, key: StorageKey, part: Literal['data', 'state', 'lock'] | None = None) -> str:
        parts = [getenv("WEB_ID")]

        # Put user first (or rearrange as you wish)
        parts.append(f"c{key.chat_id if key.chat_id is not None else '0'}")
        parts.append(f"u{key.user_id if key.user_id is not None else '0'}")
        parts.append(part)
        return ":".join(parts)

def register_routers(dp: Dispatcher) -> None:
    """Registers routers"""
    dp.include_router(command_router)
    dp.include_router(callback_router)
    dp.include_router(message_router)


async def main() -> None:
    """The main function which will execute our event loop and start polling."""
    redis_client = redis.Redis(host=getenv("REDIS_HOST"), port=getenv("REDIS_PORT"), password=getenv("REDIS_PASSWORD"), socket_connect_timeout=3)
    await redis_client.ping()
    logger.info("Redis Engine Ready! Vroom. Vroom.")
    redis_storage = RedisStorage(redis=redis_client, key_builder=RedisKeyBuilder())
    
    config = BotConfig(web_id=WEB_ID, site_name=SITE_NAME, whitelist_mode=WHITELIST_MODE, whitelist_ids=WHITELIST_IDS, otp_host=OTP_HOST)

    dp = Dispatcher(storage=redis_storage)
    dp["config"] = config

    register_routers(dp)

    bot_username = (await bot.get_me()).username

    #https://emojicombos.com/ascii-art
    logger.info(r"""
⠀      (\__/)
       (•ㅅ•)      System is running...
    ＿ノヽ ノ＼＿      using polling method.
 `/ `/ ⌒Ｙ⌒ Ｙ ヽ     with redis storage.
 (  (三ヽ人　 /　 |     Running as @%s (https://t.me/%s)
 | ﾉ⌒＼ ￣￣ヽ  ノ     Site Name: "%s"
 ヽ＿＿＿＞､＿_／       Meoww.. *** I'm a catto !!! ***
     ｜( 王 ﾉ〈    (\__/)
     / ﾐ`ー―彡 \   (•ㅅ•)
    /  ╰    ╯   \  /    \>
""", bot_username, bot_username, SITE_NAME)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logger.info("Burning up the Engine...")
    asyncio.run(main())