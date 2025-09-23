from aiogram import Router, types
from aiogram import F 
from aiogram.filters import MagicData

from bot_instance import GlobalStates
from handlers.messages.msg_contact import msg_contact
from handlers.middlewares.verify_contact import VerifyContactMiddleware
from handlers.messages.msg_register import msg_register_1_username, msg_register_2_password, msg_register_3_bank_name, msg_register_4_bank_account_name, msg_register_5_bank_account_number


message_router = Router()

# Add contact verification middleware to all message handlers
message_router.message.middleware(VerifyContactMiddleware())

# Contact message handler
message_router.message.register(msg_contact, F.contact)
message_router.message.register(msg_register_1_username, GlobalStates.register_1_ask_username)
message_router.message.register(msg_register_2_password, GlobalStates.register_2_ask_password)
message_router.message.register(msg_register_3_bank_name, GlobalStates.register_3_ask_bank_name)
message_router.message.register(msg_register_4_bank_account_name, GlobalStates.register_4_ask_bank_account_name)
message_router.message.register(msg_register_5_bank_account_number, GlobalStates.register_5_ask_bank_account_number)
# message_router.message.register(msg_register_6_confirm_register, GlobalStates.register_6_ask_confirm_register)
