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
from handlers.multi import multi_menu
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

def get_logged_in_menu_builder() -> ReplyKeyboardBuilder:
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="Menu"))
    builder.add(KeyboardButton(text="Deposit"))
    builder.add(KeyboardButton(text="Withdraw"))
    builder.add(KeyboardButton(text="Logout"))
    builder.adjust(2)
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
    login_model = ModelLogin(state=state, chat_id=chat_id, initiator_message_id=message_id)
    if isinstance(callback, Message):
        login_model.add_message_id(message_id)
    await login_model.save_to_state()

    api_client = OTPAPIClient(state=state, user_id=callback.from_user.id, base_url=config.otp_host)

    try:
        # Make POST request to ask-login endpoint
        response = await api_client.ask_auth()

        if response.is_error:
            error_message = f"🚨 Gagal memulai proses login 🚨\nError: {response.get_error_message()}"
            if isinstance(callback, CallbackQuery):
                await callback.answer()
                await callback.message.answer(error_message)
                return
            elif isinstance(callback, Message):
                await callback.answer(error_message)
                return
    
        # Success case - check if captcha is required
        captcha_required = response.data.get('captcha', False) if response.data else False
        login_model.is_required_captcha = captcha_required
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="❌ Batalkan", callback_data="login_cancel"))
        login_model.add_message_id((await bot.send_message(chat_id, """
Silahkan kirimkan username
""", reply_markup=builder.as_markup())).message_id)

        await state.set_state(GuestStates.login_1_ask_username)
                
    except Exception as e:
        login_model.add_message_id((await bot.send_message(chat_id, "Terjadi kesalahan sistem")).message_id)
    finally:
        await login_model.save_to_state()

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

    await callback_auth_clear(config, state)
    
    if isinstance(callback, CallbackQuery):
        return await multi_menu.guest_menu(callback.message, config, state)
    else:
        return await multi_menu.guest_menu(callback, config, state)

'''
Login Cancel Function

Entrypoint:
- Callback Router (data: login_cancel)
'''
async def login_cancel(callback: CallbackQuery, config: BotConfig, state: FSMContext):
    await callback.answer("Proses login dibatalkan")
    return await callback_auth_clear(config, state)

'''
Login Submit Username Function

Entrypoint:
- Message Router (text: username)
'''
async def login_submit_username(callback: Message, config: BotConfig, state: FSMContext):
    login_model: ModelLogin | None = await model_utils.load_model(ModelLogin, state)
    if login_model is None:
        return
    login_model.add_message_id(callback.message_id)
    login_model.username = callback.text

    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="❌ Batalkan", callback_data="login_cancel"))
    login_model.add_message_id((await callback.answer("Silahkan kirimkan password", reply_markup=builder.as_markup())).message_id)
    await state.set_state(GuestStates.login_2_ask_password)

'''
Login Submit Password Function

Entrypoint:
- Message Router (text: password)
'''
async def login_submit_password(callback: Message, config: BotConfig, state: FSMContext):
    login_model: ModelLogin | None = await model_utils.load_model(ModelLogin, state)
    if login_model is None:
        await callback.reply("Silahkan ulangi proses login")
        return

    login_model.add_message_id(callback.message_id)
    login_model.password = callback.text

    if login_model.is_required_captcha:
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="❌ Batalkan", callback_data="login_cancel"))
        
        login_model.add_message_id((await callback.answer("Silahkan kirimkan captcha", reply_markup=builder.as_markup())).message_id)
        await state.set_state(GuestStates.login_3_ask_captcha)
        await login_model.save_to_state()
    else:
        return await login_submit(callback, config, state, login_model)

async def login_submit_captcha(callback: Message, config: BotConfig, state: FSMContext, login_model: ModelLogin):
    login_model: ModelLogin | None = await model_utils.load_model(ModelLogin, state)
    if login_model is None:
        await callback.reply("Silahkan ulangi proses login")
        return

    login_model.add_message_id(callback.message_id)
    login_model.captcha = callback.text
    await login_model.save_to_state()
    return await login_submit(callback, config, state, login_model)

'''
Login Submit Function

Entrypoint:
- self.login_submit_password()
- self.login_submit_captcha()
'''
async def login_submit(callback: Message, config: BotConfig, state: FSMContext, login_model: ModelLogin):
    await login_model.delete_all_messages()
    api_client = OTPAPIClient(state=state, user_id=callback.from_user.id, base_url=config.otp_host)
    response = await api_client.submit_login(login_model.dump_data())

    if response.is_error:
        login_model.add_message_id((await callback.answer(f"{response.get_error_message()}")).message_id)
        login_model.add_message_id((await callback.answer(f"Silahkan ulangi proses login dengan mengetik /login")).message_id)
        
        if response.has_validation_errors:
            for field, errors in response.metadata.get('validation', {}).items():
                for error in errors:
                    login_model.add_message_id((await callback.answer(f"Validasi Error: {error}")).message_id)
        await login_model.save_to_state()
        await state.set_state(None)
        return

    user_model = ModelUser(
        **response.data,
        state=state,
        chat_id=callback.chat.id,
        is_authenticated=True,
    )
    await user_model.save_to_state()
    await state.set_state(LoggedInStates.main_menu)
    user_model.add_message_id((await callback.answer("Login berhasil", reply_markup=get_logged_in_menu_builder().as_markup(resize_keyboard=True))).message_id)

    await callback_auth_clear(config, state)

    # Redirect to authenticated /start command
    await multi_menu.logged_in_menu(callback, config, state, user_model)
    return response.data

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
    response = await api_client.ask_auth()
    if response.is_error:
        error_message = f"🚨 Gagal memulai proses register 🚨\nError: {response.get_error_message()}"
        if isinstance(callback, CallbackQuery):
            await callback.answer()
            await callback.message.answer(error_message)
            return
        elif isinstance(callback, Message):
            await callback.answer(error_message)
            return

    chat_id: int | None = None
    message_id: int | None = None
    if isinstance(callback, CallbackQuery):
        await callback.answer("Memulai proses register...")
        chat_id = callback.message.chat.id
        message_id = callback.message.message_id
    elif isinstance(callback, Message):
        chat_id = callback.chat.id
        message_id = callback.message_id

    register_model = ModelRegister(
        state=state,
        chat_id=chat_id,
        bank_list=response.data.get("bank_list", []),
        is_required_captcha=response.data.get("captcha", False),
        phone_number=telegram_data.contact_phone,
    )

    if isinstance(callback, Message):
        register_model.add_message_id(message_id)

    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="❌ Batalkan", callback_data="register_cancel"))
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