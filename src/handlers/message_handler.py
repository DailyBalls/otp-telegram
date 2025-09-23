from aiogram import Router, types
from aiogram import F 
from aiogram.filters import MagicData

from handlers.messages.msg_contact import msg_contact


message_router = Router()

# Contact message handler
message_router.message.register(msg_contact, F.contact)