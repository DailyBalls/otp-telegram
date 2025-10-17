from aiogram import types
from aiogram.fsm.context import FSMContext

from config import BotConfig
from models.model_user import ModelUser
from services.otp_services.api_client import OTPAPIClient
import utils.models as model_utils

async def callback_logout(callback: types.CallbackQuery, config: BotConfig, state: FSMContext) -> None:
    api_client = OTPAPIClient(state=state, user_id=callback.from_user.id, base_url=config.otp_host)
    logout = await api_client.logout()
    
    # Check if user has already verified their contact
    user_model: ModelUser | None = await model_utils.load_model(ModelUser, state)
    if user_model:
        await user_model.logout()
        await user_model.delete_from_state()

    await callback.message.answer("Berhasil logout")
    await callback.answer("Logout berhasil")
    return