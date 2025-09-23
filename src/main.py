import asyncio
from os import getenv
from dotenv import load_dotenv

from handlers.command_router import command_router
from handlers.message_handler import message_router
load_dotenv()

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

from bot_instance import bot
from config import BotConfig



TOKEN = getenv("BOT_TOKEN")
WHITELIST_MODE = str(getenv("WHITELIST_MODE")).lower() == "true"
SERVER_NAME = getenv("SERVER_NAME")
WHITELIST_IDS = [ 
    
]

dp = Dispatcher()


# # Command handler
# @dp.message(Command("start"))
# async def command_start_handler(message: Message) -> None:
#     await message.answer("Hello! I'm a bot created with aiogram.")


def register_routers(dp: Dispatcher) -> None:
    """Registers routers"""

    dp.include_router(command_router)
    dp.include_router(message_router)


async def main() -> None:
    """The main function which will execute our event loop and start polling."""
    
    config = BotConfig(server_name=SERVER_NAME, whitelist_mode=WHITELIST_MODE, whitelist_ids=WHITELIST_IDS)
    dp = Dispatcher()
    dp["config"] = config

    register_routers(dp)
    
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())