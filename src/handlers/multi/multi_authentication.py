from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.types.callback_query import CallbackQuery
from aiogram.types.inline_keyboard_button import InlineKeyboardButton
from aiogram.types.message import Message
from aiogram.fsm.context import FSMContext
from aiogram.types.message_auto_delete_timer_changed import MessageAutoDeleteTimerChanged
from aiogram.types.reply_keyboard_remove import ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from config import BotConfig
from handlers.callbacks.callback_auth import callback_auth_clear
from handlers.commands.cmd_action import cmd_start_authenticated
from keyboards.inline import keyboard_guest
from models.model_login import ModelLogin
from models.model_register import ModelRegister
from models.model_telegram_data import ModelTelegramData
from models.model_user import ModelUser
from services.otp_services.api_client import OTPAPIClient
import utils.models as model_utils
from bot_instance import GuestStates, LoggedInStates, bot

def get_guest_menu_builder() -> ReplyKeyboardBuilder:
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="Login"))
    builder.add(KeyboardButton(text="Register"))
    builder.adjust(2)  # One button per row
    return builder

'''
Login Init Function

Entrypoint:
- Message Router (text: login)
- Command Router (cmd: login)
- Callback Router (data: login)
'''
async def login_init(callback: CallbackQuery | Message, config: BotConfig, state: FSMContext):
    user_model: ModelUser | None = await model_utils.load_model(ModelUser, state)
    chat_id: int | None = None
    message_id: int | None = None
    if isinstance(callback, CallbackQuery):
        if user_model is not None:
            await callback.message.delete()
            await callback.answer("Silahkan logout terlebih dahulu")
            return
        chat_id = callback.message.chat.id
        message_id = callback.message.message_id
        await callback.answer("Memulai proses login...")

    elif isinstance(callback, Message):
        if user_model is not None:
            await callback.reply("Silahkan logout terlebih dahulu")
            return
        chat_id = callback.chat.id
        message_id = callback.message_id
    
    await callback_auth_clear(config, state)
    login_model = ModelLogin(state=state, chat_id=chat_id)
    if isinstance(callback, Message):
        login_model.add_message_id(message_id)
    await login_model.save_to_state()

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
                builder = InlineKeyboardBuilder()
                builder.add(InlineKeyboardButton(text="Batalkan", callback_data="login_cancel"))
                login_model.add_message_id((await bot.send_message(chat_id, """
Silahkan kirimkan username dan password dengan format: username:password
Contoh: fulan:rahasia
""", reply_markup=builder.as_markup())).message_id)

                await state.set_state(GuestStates.login_1_ask_credentials)
        else:
            login_model.add_message_id((await bot.send_message(chat_id, "Gagal memulai proses login")).message_id)
            login_model.add_message_id((await bot.send_message(chat_id, f"Error: {response.get_error_message()}")).message_id)

    except Exception as e:
        login_model.add_message_id((await bot.send_message(chat_id, "Terjadi kesalahan sistem")).message_id)

'''
Logout Function

Entrypoint:
- Message Router (text: logout)
- Command Router (cmd: logout)
- Callback Router (data: logout)
'''
async def logout(callback: CallbackQuery | Message, config: BotConfig, state: FSMContext):
    user_model: ModelUser | None = await model_utils.load_model(ModelUser, state)
    if user_model is not None:
        await user_model.logout()
        await user_model.delete_from_state()
    
    await state.set_state(None)
    message_id: int | None = None
    chat_id: int | None = None
    if isinstance(callback, CallbackQuery):
        await callback.answer("Logout berhasil")
        message_id = callback.message.message_id
        chat_id = callback.message.chat.id
    elif isinstance(callback, Message):
        message_id = callback.message_id
        chat_id = callback.chat.id

    await bot.send_message(chat_id, "Logout berhasil", reply_markup=get_guest_menu_builder().as_markup(resize_keyboard=True))

    return await callback_auth_clear(config, state)

'''
Login Cancel Function

Entrypoint:
- Callback Router (data: login_cancel)
'''
async def login_cancel(callback: CallbackQuery, config: BotConfig, state: FSMContext):
    await callback.answer("Proses login dibatalkan")
    return await callback_auth_clear(config, state)

'''
Login Submit Credentials Function

Entrypoint:
- Message Router (text: username:password)
'''
async def login_submit_credentials(callback: Message, config: BotConfig, state: FSMContext):
    await callback.delete()
    login_model: ModelLogin | None = await model_utils.load_model(ModelLogin, state)
    if login_model is None:
        return
    
    if callback.text.count(":") != 1:
        login_model.add_message_id((await callback.answer("Format tidak valid, silahkan kirimkan username dan password dengan format: \n<code>username:password</code>")).message_id)
        return

    username, password = callback.text.split(":")
    api_client = OTPAPIClient(state=state, user_id=callback.from_user.id, base_url=config.otp_host)
    response = await api_client.submit_login({"username": username, "password": password})
    
    username, password = callback.text.split(":")
    api_client = OTPAPIClient(state=state, user_id=callback.from_user.id, base_url=config.otp_host)
    response = await api_client.submit_login({"username": username, "password": password})
    
    if response.is_error:
        login_model.add_message_id((await callback.answer(f"{response.get_error_message()}")).message_id)
        if response.has_validation_errors:
            for field, errors in response.metadata.get('validation', {}).items():
                for error in errors:
                    login_model.add_message_id((await callback.answer(f"Validasi Error: {error}")).message_id)
        return

    user_model = ModelUser(
        **response.data,
        state=state,
        chat_id=callback.chat.id,
        is_authenticated=True,
    )
    await user_model.save_to_state()
    await state.set_state(LoggedInStates.main_menu)
    reply_keyboard = ReplyKeyboardRemove()
    user_model.add_message_id((await callback.answer("Login berhasil", reply_markup=reply_keyboard)).message_id)

    await callback_auth_clear(config, state)

    # Redirect to authenticated /start command
    await cmd_start_authenticated(callback, config, state, user_model)

'''
Register Init Function

Entrypoint:
- Message Router (text: register)
- Command Router (cmd: register)
- Callback Router (data: register)
'''
async def register_init(callback: CallbackQuery | Message, config: BotConfig, state: FSMContext, telegram_data: ModelTelegramData) -> None:
    await callback_auth_clear(config, state)
    user_model: ModelUser | None = await model_utils.load_model(ModelUser, state)
    if user_model is not None:
        if isinstance(callback, CallbackQuery):
            await callback.answer("Silahkan logout terlebih dahulu")
            return
        elif isinstance(callback, Message):
            await callback.reply("Silahkan logout terlebih dahulu")
            return

    api_client = OTPAPIClient(state=state, user_id=callback.from_user.id, base_url=config.otp_host)
    ask_auth = await api_client.ask_auth()
    if ask_auth.is_error:
        if isinstance(callback, CallbackQuery):
            await callback.answer(f"Gagal memulai proses register")
        elif isinstance(callback, Message):
            await callback.reply(f"Gagal memulai proses register")
        print("There is an error when asking for auth to OTP API", ask_auth.error)
        return
 
    if isinstance(callback, CallbackQuery):
        await callback.answer("Memulai proses register...")

    chat_id: int | None = None
    message_id: int | None = None
    if isinstance(callback, CallbackQuery):
        chat_id = callback.message.chat.id
        message_id = callback.message.message_id
    elif isinstance(callback, Message):
        chat_id = callback.chat.id
        message_id = callback.message_id

    register_model = ModelRegister(
        state=state,
        chat_id=chat_id,
        bank_list=ask_auth.data.get("bank_list", []),
        is_required_captcha=ask_auth.data.get("captcha", False),
        phone_number=telegram_data.contact_phone,
    )

    if isinstance(callback, Message):
        register_model.add_message_id(message_id)

    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Batalkan", callback_data="register_cancel"))
    register_model.add_message_id((await bot.send_message(chat_id, "Silahkan kirimkan username", reply_markup=builder.as_markup())).message_id)
    await register_model.save_to_state()
    await state.set_state(GuestStates.register_1_ask_username)

'''
Register Cancel Function

Entrypoint:
- Callback Router (data: register_cancel)
'''
async def register_cancel(callback: CallbackQuery, config: BotConfig, state: FSMContext):
    await callback.answer("Proses register dibatalkan")
    return await callback_auth_clear(config, state)