from aiogram import Router, types
from aiogram.types.contact import Contact
from aiogram.fsm.context import FSMContext
from aiogram.types.inline_keyboard_button import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import BotConfig
from models.model_action import ModelAction
from models.model_user import ModelUser
import utils.validators as validators
from bot_instance import LoggedInStates
from keyboards.inline import keyboard_guest
import utils.models as model_utils

async def msg_withdraw_ask_amount(msg: types.Message, config: BotConfig, state: FSMContext, user_model: ModelUser) -> None:
    action_model: ModelAction | None = await model_utils.load_model(ModelAction, state)
    if action_model is None:
        reply = await msg.answer("Silahkan ulangi proses withdraw")
        action_model.add_message_id(reply.message_id)
        user_model.add_message_id(reply.message_id)
        return
    
    action_model.add_message_id(msg.message_id)
    user_model.add_message_id(msg.message_id)
    
    

    return
