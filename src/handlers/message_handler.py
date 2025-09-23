from aiogram import Router, types
from aiogram import F 
from aiogram.filters import MagicData

from handlers.messages.msg_contact import msg_contact
from handlers.middlewares.verify_contact import VerifyContactMiddleware


message_router = Router()

# Add contact verification middleware to all message handlers
message_router.message.middleware(VerifyContactMiddleware())

# Contact message handler
message_router.message.register(msg_contact, F.contact)