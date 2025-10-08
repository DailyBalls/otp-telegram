from aiogram import types
from aiogram.fsm.context import FSMContext

from bot_instance import GuestStates, bot
from config import BotConfig
from handlers.messages.msg_register import send_confirmation_register_message
from keyboards.inline import keyboard_auth
from models.model_login import ModelLogin
from models.model_register import ModelRegister
from models.model_user import ModelUser
from services.otp_services.api_client import OTPAPIClient
import utils.models as model_utils

async def callback_auth_clear(callback: types.CallbackQuery, config: BotConfig, state: FSMContext) -> None:
    login_model: ModelLogin | None = await model_utils.load_model(ModelLogin, state)
    if login_model:
        await login_model.delete_all_messages()
        await login_model.delete_from_state()
    
    register_model: ModelRegister | None = await model_utils.load_model(ModelRegister, state)
    if register_model:
        await register_model.delete_all_messages()
        await register_model.delete_from_state()

    return