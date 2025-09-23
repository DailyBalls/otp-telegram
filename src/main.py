from os import getenv
from dotenv import load_dotenv
load_dotenv()

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



TOKEN = getenv("BOT_TOKEN")
WHITELIST_MODE = str(getenv("WHITELIST_MODE")).lower() == "true"
SERVER_NAME = getenv("SERVER_NAME")
WHITELIST_IDS = [ 
    
]


def register_routers(dp: Dispatcher) -> None:
    """Registers routers"""
    dp.include_router(command_router)
    dp.include_router(callback_router)
    dp.include_router(message_router)


async def main() -> None:
    """The main function which will execute our event loop and start polling."""
    redis_client = redis.Redis(host=getenv("REDIS_HOST"), port=getenv("REDIS_PORT"), password=getenv("REDIS_PASSWORD"), socket_connect_timeout=3)
    await redis_client.ping()
    print("Redis Engine Ready! Vroom. Vroom.")
    redis_storage = RedisStorage(redis=redis_client)
    
    config = BotConfig(server_name=SERVER_NAME, whitelist_mode=WHITELIST_MODE, whitelist_ids=WHITELIST_IDS)

    dp = Dispatcher(storage=redis_storage)
    dp["config"] = config

    register_routers(dp)
    
    print(f"""
⠀      (\__/)
       (•ㅅ•)      Bot is running...
    ＿ノヽ ノ＼＿      using polling.
 `/ `/ ⌒Ｙ⌒ Ｙ  ヽ     with redis storage.
 (  (三ヽ人　 /　|
 | ﾉ⌒＼ ￣￣ヽ  ノ
 ヽ＿＿＿＞､＿_／       Meoww..
     ｜( 王 ﾉ〈    (\__/)
     / ﾐ`ー―彡 \   (•ㅅ•)
    /  ╰    ╯   \  /    \>
""")
    await dp.start_polling(bot)


if __name__ == "__main__":
    print("Burning up the Engine...")
    asyncio.run(main())