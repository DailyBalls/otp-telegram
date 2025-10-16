import base64
from aiogram import Router, types
from aiogram.types.contact import Contact
from aiogram.fsm.context import FSMContext
from aiogram.types.inline_keyboard_button import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import BotConfig
from models.model_games import AvailableGames
from models.model_user import ModelUser
from services.otp_services.api_client import OTPAPIClient
import utils.validators as validators
from bot_instance import LoggedInStates
from keyboards.inline import keyboard_guest
import utils.models as model_utils
from handlers.callbacks.callback_game import _game_search

async def msg_game_search(msg: types.Message, config: BotConfig, state: FSMContext, api_client: OTPAPIClient, user_model: ModelUser) -> None:
    if msg.text is None:
        user_model.add_message_id((await msg.answer("Silahkan kirimkan pencarian game")).message_id)
        user_model.save_to_state()
        return
    
    await state.set_state(LoggedInStates.main_menu)
    search_base64 = base64.b64encode(msg.text.encode()).decode()
    await _game_search(user_model, search_base64, 1, api_client, msg.chat.id)
    return