from aiogram import types
from aiogram.fsm.context import FSMContext

from bot_instance import GuestStates
from config import BotConfig
from services.otp_services.api_client import OTPAPIClient

async def callback_login(callback: types.CallbackQuery, config: BotConfig, state: FSMContext) -> None:
    await callback.answer()
    
    # Initialize API client with user's Telegram ID and OTP host
    api_client = OTPAPIClient(state=state, base_url=config.otp_host)
    
    try:
        # Make POST request to ask-login endpoint
        response = await api_client.ask_auth()
        
        if response.success:
            # Success case - check if captcha is required
            captcha_required = response.data.get('captcha', False) if response.data else False
            
            if captcha_required:
                await callback.message.answer("Please complete the captcha first")
            else:
                await callback.message.answer("Silahkan kirimkan username dan password")
                await state.set_state(GuestStates.login_1_ask_credentials)
        else:
            # Error case - handle validation errors
            if response.has_validation_errors:
                telegram_id_errors = response.get_field_errors('telegram_id')
                if telegram_id_errors:
                    await callback.message.answer(f"Error: {response.get_first_field_error('telegram_id')}")
                else:
                    await callback.message.answer("Terjadi kesalahan validasi")
            else:
                await callback.message.answer(f"Error: {response.get_error_message()}")
                
    except Exception as e:
        await callback.message.answer("Terjadi kesalahan sistem")
