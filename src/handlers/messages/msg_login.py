from aiogram import Router, types
from aiogram.types.contact import Contact
from aiogram.fsm.context import FSMContext
from aiogram.types.inline_keyboard_button import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import BotConfig
from handlers.callbacks.callback_auth import callback_auth_clear
from models.model_login import ModelLogin
from models.model_user import ModelUser
from services.otp_services.api_client import OTPAPIClient
import utils.validators as validators
from bot_instance import GuestStates, LoggedInStates
from keyboards.inline import keyboard_auth
import utils.models as model_utils
from handlers.commands.cmd_start import cmd_start_authenticated

async def msg_login_1_ask_credentials(msg: types.Message, config: BotConfig, state: FSMContext) -> None:
    login_model = await model_utils.load_model(ModelLogin, state)
    if not login_model:
        login_model = ModelLogin(state=state, chat_id=msg.chat.id)
        await login_model.save_to_state()

    login_model.add_message_id(msg.message_id)

    cancel_builder = keyboard_auth.auth_cancel()
    if msg.text is None:
        login_model.add_message_id((await msg.answer("Silahkan kirimkan username dan password dengan format: username:password", reply_markup=cancel_builder.as_markup())).message_id)
        return

    if not validators.min_length(msg.text, 6):
        login_model.add_message_id((await msg.answer("Username dan password tidak valid", reply_markup=cancel_builder.as_markup())).message_id)
        return

    username, password = msg.text.split(":")
    api_client = OTPAPIClient(state=state, user_id=msg.from_user.id, base_url=config.otp_host)
    response = await api_client.submit_login({"username": username, "password": password})
    
    if response.is_error:
        login_model.add_message_id((await msg.answer(f"{response.get_error_message()}")).message_id)
        if response.has_validation_errors:
            for field, errors in response.metadata.get('validation', {}).items():
                for error in errors:
                    login_model.add_message_id((await msg.answer(f"Validasi Error: {error}")).message_id)
        return

    print("response from OTP API", response.data)
    user_model = ModelUser(
        state=state,
        username=username,
        chat_id=msg.chat.id,
        is_authenticated=True,
        credit=response.data.get("credit", 0),
        rank=response.data.get("rank", "Unranked"),
    )
    await user_model.save_to_state()
    await state.set_state(LoggedInStates.main_menu)
    user_model.add_message_id((await msg.answer("Login berhasil")).message_id)

    await callback_auth_clear(msg, config, state)

    # Redirect to authenticated /start command
    await cmd_start_authenticated(msg, config, state, user_model)

    