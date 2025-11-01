from aiogram import types
from aiogram.fsm.context import FSMContext

from config import BotConfig
from models.model_login import ModelLogin
from models.model_register import ModelRegister
import utils.models as model_utils
from utils.logger import get_logger

logger = get_logger()

async def callback_auth_clear(config: BotConfig, state: FSMContext) -> None:
    login_model: ModelLogin | None = await model_utils.load_model(ModelLogin, state)
    if login_model:
        logger.debug(f"Deleting login messages: {login_model.list_messages_ids}")
        await login_model.delete_all_messages()
        await login_model.delete_from_state()
    
    register_model: ModelRegister | None = await model_utils.load_model(ModelRegister, state)
    if register_model:
        logger.debug(f"Deleting register messages: {register_model.list_messages_ids}")
        await register_model.delete_all_messages()
        await register_model.delete_from_state()

    return