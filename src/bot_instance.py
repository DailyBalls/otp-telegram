

from aiogram import Bot, types
from os import getenv
from aiogram.client.default import DefaultBotProperties

from aiogram.fsm.state import State, StatesGroup

class GuestStates(StatesGroup):

    register_1_ask_username             = State()
    register_1_edit_username            = State()
    register_2_ask_password             = State()
    register_2_edit_password            = State()
    register_3_ask_bank_name            = State()
    register_3_edit_bank_name           = State()
    register_4_ask_bank_account_name    = State()
    register_4_edit_bank_account_name   = State()
    register_5_ask_bank_account_number  = State()
    register_5_edit_bank_account_number = State()
    register_6_ask_confirm_register     = State()
    
    login_1_ask_credentials             = State()

class LoggedInStates(StatesGroup):
    
    main_menu = State()
    deposit_ask_amount = State()
    deposit_ask_method = State()
    deposit_ask_channel_payment_gateway = State()
    deposit_confirm = State()
    deposit_confirm_channel = State()
    
    withdraw_ask_amount = State()
    
    game_search = State()

    rekening_add_1_ask_bank_name = State()
    rekening_add_2_ask_bank_account_name = State()
    rekening_add_3_ask_bank_account_number = State()
    rekening_add_4_ask_confirm_add = State()



bot = Bot(
    token=str(getenv("BOT_TOKEN")),
    default=DefaultBotProperties(parse_mode='HTML')
)