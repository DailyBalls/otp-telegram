from aiogram import types
from aiogram.fsm.context import FSMContext

from bot_instance import GuestStates, bot
from config import BotConfig
from handlers.callbacks.callback_auth import callback_auth_clear
from models.model_login import ModelLogin
from models.model_user import ModelUser
from services.otp_services.api_client import OTPAPIClient
import utils.models as model_utils

async def callback_login(callback: types.CallbackQuery, config: BotConfig, state: FSMContext) -> None:
    user_model = await model_utils.load_model(ModelUser, state)
    if user_model is not None:
        await callback.answer("Silahkan logout terlebih dahulu")
        await bot.delete_message(callback.message.chat.id, callback.message.message_id)
        return

    await callback.answer("Memulai proses login...")

    await callback_auth_clear(callback, config, state)
    
    login_model = ModelLogin(state=state, chat_id=callback.message.chat.id)
    # Initialize API client with user's Telegram ID and OTP host
    api_client = OTPAPIClient(state=state, user_id=callback.from_user.id, base_url=config.otp_host)
    
    try:
        # Make POST request to ask-login endpoint
        response = await api_client.ask_auth()
        
        if response.success:
            # Success case - check if captcha is required
            captcha_required = response.data.get('captcha', False) if response.data else False
            
            if captcha_required:
                pass # TODO: Handle captcha
            else:
                login_model.add_message_id((await callback.message.answer("""
Silahkan kirimkan username dan password dengan format: username:password
Contoh: fulan:rahasia
""")).message_id)

                await state.set_state(GuestStates.login_1_ask_credentials)
        else:
            login_model.add_message_id((await callback.message.answer("Gagal memulai proses login")).message_id)
            login_model.add_message_id((await callback.message.answer(f"Error: {response.get_error_message()}")).message_id)
                
    except Exception as e:
        login_model.add_message_id((await callback.message.answer("Terjadi kesalahan sistem")).message_id)
