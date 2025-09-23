from aiogram import Bot, types
from os import getenv
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

bot = Bot(
    token=str(getenv("BOT_TOKEN")),
    default=DefaultBotProperties(parse_mode='HTML')
)