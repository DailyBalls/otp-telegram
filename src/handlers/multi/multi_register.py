from aiogram.types.callback_query import CallbackQuery
from aiogram.types.inline_keyboard_button import InlineKeyboardButton
from aiogram.types.message import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import BotConfig
from handlers.callbacks.callback_auth import callback_auth_clear
from models.model_register import ModelRegister
from models.model_telegram_data import ModelTelegramData
from models.model_user import ModelUser
from services.otp_services.api_client import OTPAPIClient
import utils.models as model_utils
from bot_instance import GuestStates, bot
from aiogram.fsm.context import FSMContext

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