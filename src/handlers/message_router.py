from aiogram import Router, types
from aiogram import F 

from bot_instance import GuestStates, LoggedInStates
from handlers.messages.msg_contact import msg_contact
from handlers.messages.msg_rekening import msg_rekening_ask_bank_account_number
from handlers.middlewares.authenticated_session import AuthenticatedSessionMiddleware
from handlers.middlewares.verify_contact import VerifyContactMiddleware
from handlers.middlewares.register_middleware import RegisterSessionMiddleware
from handlers.messages.msg_register import msg_register_1_username, msg_register_2_password, msg_register_3_bank_name, msg_register_4_bank_account_name, msg_register_5_bank_account_number
from handlers.messages.msg_deposit import msg_deposit_ask_amount
from handlers.messages.msg_game import msg_game_search

from handlers.multi import multi_login, multi_register, multi_deposit, multi_menu, multi_withdraw
from utils.filters import StatesGroup, Text
from handlers.middlewares.verify_private_chat import VerifyPrivateChatMiddleware

message_router = Router()
# Validate if chat came only from Private Chat
message_router.message.middleware(VerifyPrivateChatMiddleware())
# Add contact verification middleware to all message handlers
message_router.message.middleware(VerifyContactMiddleware())
message_router.message.filter(~F.text.startswith("/"))
message_router.message.register(msg_contact, F.contact)
message_router.message.register(multi_login.logout, Text(data="logout"))

guest_router = Router()
guest_router.message.filter(~StatesGroup(LoggedInStates)) # ~ = Not in LoggedInStates
guest_router.message.register(multi_login.login_init, Text(data="login"))
guest_router.message.register(multi_register.register_init, Text(data="register"))
guest_router.message.register(multi_menu.guest_menu, Text(data="menu"))
message_router.include_router(guest_router)

login_router = Router()
login_router.message.register(multi_login.login_submit_username, GuestStates.login_1_ask_username)
login_router.message.register(multi_login.login_submit_password, GuestStates.login_2_ask_password)
login_router.message.register(multi_login.login_submit_captcha, GuestStates.login_3_ask_captcha)
message_router.include_router(login_router)

# Contact message handler
register_router = Router()
register_router.message.filter(StatesGroup(GuestStates))
register_router.message.middleware(RegisterSessionMiddleware())
register_router.message.register(msg_register_1_username, GuestStates.register_1_ask_username)
register_router.message.register(msg_register_1_username, GuestStates.register_1_edit_username)
register_router.message.register(msg_register_2_password, GuestStates.register_2_ask_password)
register_router.message.register(msg_register_2_password, GuestStates.register_2_edit_password)
register_router.message.register(msg_register_3_bank_name, GuestStates.register_3_ask_bank_name)
register_router.message.register(msg_register_3_bank_name, GuestStates.register_3_edit_bank_name)
register_router.message.register(msg_register_4_bank_account_name, GuestStates.register_4_ask_bank_account_name)
register_router.message.register(msg_register_4_bank_account_name, GuestStates.register_4_edit_bank_account_name)
register_router.message.register(msg_register_5_bank_account_number, GuestStates.register_5_ask_bank_account_number)
register_router.message.register(msg_register_5_bank_account_number, GuestStates.register_5_edit_bank_account_number)
message_router.include_router(register_router)


authenticated_router = Router()
authenticated_router.message.filter(StatesGroup(LoggedInStates))

## Menu Message Handlers
authenticated_router.message.middleware(AuthenticatedSessionMiddleware())
authenticated_router.message.register(multi_login.logout, Text(data="logout"))
authenticated_router.message.register(multi_menu.logged_in_menu, Text(data="menu"))
authenticated_router.message.register(multi_withdraw.withdraw_init, Text(data="withdraw"))
authenticated_router.message.register(multi_deposit.deposit_init, Text(data="deposit"))
authenticated_router.message.register(multi_deposit.deposit_submit_note, LoggedInStates.deposit_ask_note)

## Action Message Handlers
authenticated_router.message.register(multi_deposit.deposit_submit_amount, LoggedInStates.deposit_ask_amount)
authenticated_router.message.register(msg_game_search, LoggedInStates.game_search)
# authenticated_router.message.register(msg_rekening_ask_bank_account_name, LoggedInStates.rekening_add_2_ask_bank_account_name)
authenticated_router.message.register(msg_rekening_ask_bank_account_number, LoggedInStates.rekening_add_3_ask_bank_account_number)
authenticated_router.message.register(multi_withdraw.withdraw_input_amount, LoggedInStates.withdraw_ask_amount)
message_router.include_router(authenticated_router)