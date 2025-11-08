from aiogram.types.callback_query import CallbackQuery
from aiogram.types.inline_keyboard_button import InlineKeyboardButton
from aiogram.types.message import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import BotConfig
from handlers.callbacks.callback_auth import callback_auth_clear
from keyboards.inline import keyboard_guest
from models.model_register import ModelRegister
from models.model_telegram_data import ModelTelegramData
from models.model_user import ModelUser
from services.otp_services.api_client import OTPAPIClient
from utils import validators
import utils.models as model_utils
from bot_instance import GuestStates, bot
from aiogram.fsm.context import FSMContext
from utils.logger import get_logger

logger = get_logger()
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

    return await register_ask_username(callback, config, state, chat_id, register_model)

'''
Register Ask Username Function

Entrypoint:
- register_init
'''
async def register_ask_username(callback: CallbackQuery | Message, config: BotConfig, state: FSMContext, chat_id: int, register_model: ModelRegister):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="❌ Batalkan", callback_data="register_cancel"))
    register_model.add_message_id((await bot.send_message(chat_id, "Silahkan kirimkan username", reply_markup=builder.as_markup())).message_id)
    await register_model.save_to_state()
    await state.set_state(GuestStates.register_1_ask_username)

'''
Register Submit Username Function

Entrypoint:
- Message Router (state: GuestStates.register_1_ask_username)
- Message Router (state: GuestStates.register_1_edit_username)
'''
async def register_submit_username(msg: Message, config: BotConfig, state: FSMContext, chat_id: int, register_model: ModelRegister) -> None:
    if not validators.alpha_num(msg.text):
        register_model.add_message_id((await msg.answer("Username harus berupa huruf dan angka")).message_id)
        return

    if not validators.min_length(msg.text, 6):
        register_model.add_message_id((await msg.answer("Username harus minimal 5 karakter")).message_id)
        return

    if not validators.max_length(msg.text, 16):
        register_model.add_message_id((await msg.answer("Username maksimal 16 karakter")).message_id)
        return
    
    register_model.set_username(msg.text)

    current_state = await state.get_state()
    if current_state == GuestStates.register_1_ask_username:
        return await register_ask_password(msg, config, state, chat_id, register_model)

    elif current_state == GuestStates.register_1_edit_username:
        # register_model.add_message_id((await msg.answer("Username berhasil dirubah")).message_id)
        await state.set_state(GuestStates.register_7_ask_confirm_register)
        register_model.add_message_id((await send_confirmation_register_message(chat_id, register_model)).message_id)

    return

'''
Register Ask Password Function

Entrypoint:
- register_submit_username
'''
async def register_ask_password(callback: Message, config: BotConfig, state: FSMContext, chat_id: int, register_model: ModelRegister):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="❌ Batalkan", callback_data="register_cancel"))
    register_model.add_message_id((await bot.send_message(chat_id, "Silahkan kirimkan password", reply_markup=builder.as_markup())).message_id)
    await register_model.save_to_state()
    await state.set_state(GuestStates.register_2_ask_password)

'''
Register Submit Password Function

Entrypoint:
- Message Router (state: GuestStates.register_2_ask_password)
'''
async def register_submit_password(msg: Message, config: BotConfig, state: FSMContext, chat_id: int, register_model: ModelRegister) -> None:
    if not validators.min_length(msg.text, 6):
        builder = InlineKeyboardBuilder()
        register_model.add_message_id((await msg.answer("Password harus minimal 6 karakter")).message_id)
        return

    register_model.set_password(msg.text)

    current_state = await state.get_state()
    if current_state == GuestStates.register_2_ask_password:
        await state.set_state(GuestStates.register_3_ask_bank_name)
        return await register_ask_bank_name(msg, config, state, chat_id, register_model)

    elif current_state == GuestStates.register_2_edit_password:
        await state.set_state(GuestStates.register_7_ask_confirm_register)
        register_model.add_message_id((await send_confirmation_register_message(chat_id, register_model)).message_id)

    return

'''
Register Ask Bank Name Function

Entrypoint:
- register_submit_password
'''
async def register_ask_bank_name(msg: Message, config: BotConfig, state: FSMContext, chat_id: int, register_model: ModelRegister):
    builder = keyboard_guest.bank_selection(register_model.bank_list)
    builder.add(InlineKeyboardButton(text="❌ Batalkan", callback_data="register_cancel"))
    register_model.add_message_id((await bot.send_message(chat_id, "Silahkan pilih bank yang ingin Anda gunakan", reply_markup=builder.as_markup())).message_id)
    await register_model.save_to_state()
    await state.set_state(GuestStates.register_3_ask_bank_name)

'''
Register Submit Bank Name Function

Entrypoint:
- message Router (state: GuestStates.register_3_ask_bank_name)
'''
async def register_submit_bank_name(msg: Message | CallbackQuery, config: BotConfig, state: FSMContext, chat_id: int, register_model: ModelRegister) -> None:
    if isinstance(msg, Message):
        bank_name = msg.text
    elif isinstance(msg, CallbackQuery):
        bank_name = msg.data.replace("register_bank_", "")

    # Check if register data is valid
    if register_model.bank_list is not None and bank_name not in register_model.bank_list:
        register_model.add_message_id((await bot.send_message(chat_id, f"Bank {bank_name} tidak valid")).message_id)
        return
    
    register_model.set_bank_name(bank_name)
    
    current_state = await state.get_state()
    if isinstance(msg, CallbackQuery):
        await msg.message.delete()

    register_model.add_message_id((await bot.send_message(chat_id, f"Bank <b>{bank_name}</b> berhasil dipilih")).message_id)
    if current_state == GuestStates.register_3_ask_bank_name:
        return await register_ask_rekening_name(msg, config, state, chat_id, register_model)
    elif current_state == GuestStates.register_3_edit_bank_name:
        await state.set_state(GuestStates.register_7_ask_confirm_register)
        register_model.add_message_id((await send_confirmation_register_message(chat_id, register_model)).message_id)
    return

'''
Register Ask Rekening Name Function

Entrypoint:
- register_submit_bank_name
'''
async def register_ask_rekening_name(msg: Message | CallbackQuery, config: BotConfig, state: FSMContext, chat_id: int, register_model: ModelRegister) -> None:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="❌ Batalkan", callback_data="register_cancel"))
    register_model.add_message_id((await bot.send_message(chat_id, "Silahkan kirimkan nama rekening", reply_markup=builder.as_markup())).message_id)
    await register_model.save_to_state()
    await state.set_state(GuestStates.register_4_ask_bank_account_name)

'''
Register Submit Rekening Name Function

Entrypoint:
- message Router (state: GuestStates.register_4_ask_bank_account_name)
'''
async def register_submit_rekening_name(msg: Message, config: BotConfig, state: FSMContext, chat_id: int, register_model: ModelRegister) -> None:
    # Check that the input name contains only letters (including Unicode letters) and spaces
    if not msg.text or not validators.alpha_space(msg.text):
        register_model.add_message_id((await msg.answer("Nama rekening hanya boleh berisi huruf dan spasi. Silakan kirimkan nama rekening yang valid.")).message_id)
        return
    if not validators.min_length(msg.text, 3):
        register_model.add_message_id((await msg.answer("Nama rekening harus minimal 5 karakter")).message_id)
        return

    register_model.set_bank_account_name(msg.text)
    
    current_state = await state.get_state()
    if current_state == GuestStates.register_4_ask_bank_account_name:
        # register_model.add_message_id((await msg.answer("Nama rekening berhasil diterima")).message_id)
        return await register_ask_rekening_number(msg, config, state, chat_id, register_model)
    elif current_state == GuestStates.register_4_edit_bank_account_name:
        # register_model.add_message_id((await msg.answer("Nama rekening berhasil dirubah")).message_id)
        await state.set_state(GuestStates.register_7_ask_confirm_register)
        register_model.add_message_id((await send_confirmation_register_message(chat_id, register_model)).message_id)
    return

'''
Register Ask Rekening Number Function

Entrypoint:
- register_submit_rekening_name
'''
async def register_ask_rekening_number(msg: Message | CallbackQuery, config: BotConfig, state: FSMContext, chat_id: int, register_model: ModelRegister) -> None:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="❌ Batalkan", callback_data="register_cancel"))
    register_model.add_message_id((await bot.send_message(chat_id, "Silahkan kirimkan nomor rekening", reply_markup=builder.as_markup())).message_id)
    await register_model.save_to_state()
    await state.set_state(GuestStates.register_5_ask_bank_account_number)


'''
Register Submit Bank Account Number Function

Entrypoint:
- message Router (state: GuestStates.register_5_ask_bank_account_number)
'''
async def register_submit_bank_account_number(msg: Message, config: BotConfig, state: FSMContext, chat_id: int, register_model: ModelRegister) -> None:
    if msg.text is None or not validators.numeric(msg.text):
        register_model.add_message_id((await msg.answer("Nomor rekening harus berupa angka")).message_id)
        return

    if not validators.min_length(msg.text, 8):
        register_model.add_message_id((await msg.answer("Nomor rekening harus minimal 8 digit")).message_id)
        return
    
    register_model.set_bank_account_number(msg.text)

    current_state = await state.get_state()
    if current_state == GuestStates.register_5_ask_bank_account_number:
        # register_model.add_message_id((await msg.answer("Nomor rekening berhasil diterima")).message_id)
        return await register_ask_referral_code(msg, config, state, chat_id, register_model)
    elif current_state == GuestStates.register_5_edit_bank_account_number:
        # register_model.add_message_id((await msg.answer("Nomor rekening berhasil dirubah")).message_id)
        await state.set_state(GuestStates.register_7_ask_confirm_register)
        register_model.add_message_id((await send_confirmation_register_message(chat_id, register_model)).message_id)
    await register_model.save_to_state()
    return

'''
Register Ask Referral Code Function

Entrypoint:
- register_submit_bank_account_number
'''
async def register_ask_referral_code(msg: Message | CallbackQuery, config: BotConfig, state: FSMContext, chat_id: int, register_model: ModelRegister) -> None:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="⏩ Lewati", callback_data="register_skip_referral_code"))
    register_model.add_message_id((await bot.send_message(chat_id, "Silahkan kirimkan referral code", reply_markup=builder.as_markup())).message_id)
    await register_model.save_to_state()
    await state.set_state(GuestStates.register_6_ask_referral_code)


'''
Register Submit Referral Code Function

Entrypoint:
- message Router (state: GuestStates.register_6_ask_referral_code)
'''
async def register_submit_referral_code(msg: Message | CallbackQuery, config: BotConfig, state: FSMContext, chat_id: int, register_model: ModelRegister) -> None:
    if isinstance(msg, Message):
        referral_code = msg.text
        if not validators.alpha_num(referral_code):
            register_model.add_message_id((await msg.answer("Referral code harus berupa huruf dan angka")).message_id)
            return
        register_model.set_referral_code(referral_code)
    elif isinstance(msg, CallbackQuery):
        await msg.message.edit_text(f"{msg.message.text}\n <b>Dilewati</b>", reply_markup=None)

    await state.set_state(GuestStates.register_7_ask_confirm_register)
    register_model.add_message_id((await send_confirmation_register_message(chat_id, register_model)).message_id)
    await register_model.save_to_state()
    return


'''
Send Confirmation Register Message Function

Entrypoint:
- register_submit_referral_code
'''
async def send_confirmation_register_message(chat_id: int, register_model: ModelRegister):

    builder_confirm = keyboard_guest.registration_confirm_and_edit()
    return await bot.send_message(chat_id, f"""
<b>Konfirmasi Register</b>
Username: <b>{register_model.username}</b>
Password: <b>{register_model.password}</b>
Bank: <b>{register_model.bank_name}</b>
Nama Rekening: <b>{register_model.bank_account_name}</b>
Nomor Rekening: <b>{register_model.bank_account_number}</b>
Referral Code: <b>{register_model.referral_code}</b>

Apakah data yang Anda kirimkan sudah benar?
""", reply_markup=builder_confirm.as_markup())


'''
Register Confirm Function

Entrypoint:
- register_submit_referral_code
'''
async def register_confirm_yes(callback: CallbackQuery, config: BotConfig, state: FSMContext, register_model: ModelRegister) -> None:
    api_client = OTPAPIClient(state=state, user_id=callback.from_user.id, base_url=config.otp_host)
    submit_registration = await api_client.submit_registration(register_model.get_submit_registration_data())
    if submit_registration.is_error:
        await callback.answer(f"Gagal melakukan registrasi")
        if submit_registration.has_validation_errors:
            for field, errors in submit_registration.metadata.get('validation', {}).items():
                for error in errors:
                    register_model.add_message_id((await callback.message.answer(f"Validasi Error: {error}")).message_id)
        logger.error(f"There is an error when submitting registration to OTP API - error: {submit_registration.error}, metadata: {submit_registration.metadata}")
        return
    await register_model.delete_all_messages()


'''
Register Confirm No Function

Entrypoint:
- register_confirm_no
'''
async def register_confirm_no(callback: CallbackQuery, config: BotConfig, state: FSMContext, register_model: ModelRegister) -> None:
    await callback.answer("Register dibatalkan")
    await register_model.delete_all_messages()
    await state.update_data(register=None)
    await callback_auth_clear(config, state)
    return


'''
Entrypoint:
- Callback Router (data: register_cancel)
'''
async def register_cancel(callback: CallbackQuery, config: BotConfig, state: FSMContext):
    await callback.answer("Proses register dibatalkan")
    return await callback_auth_clear(config, state)


'''
Register Edit Function

Entrypoint:
- Callback Router (data: register_edit_username)
- Callback Router (data: register_edit_password)
- Callback Router (data: register_edit_bank)
- Callback Router (data: register_edit_bank_account_name)
- Callback Router (data: register_edit_bank_account_number)
- Callback Router (data: register_edit_referral_code)
'''
async def register_edit(callback: CallbackQuery, config: BotConfig, state: FSMContext, register_model: ModelRegister) -> None:
    current_state = await state.get_state()
    # Only allow this callback if the current state is register_7_ask_confirm_register
    if(current_state != GuestStates.register_7_ask_confirm_register):
        return
    
    await bot.delete_message(callback.message.chat.id, callback.message.message_id)

    edit_type = callback.data.replace("register_edit_", "")
    if edit_type == "username":
        register_model.add_message_id((await callback.message.answer("Silahkan kirimkan username")).message_id)
        await state.set_state(GuestStates.register_1_edit_username)

    elif edit_type == "password":
        register_model.add_message_id((await callback.message.answer("Silahkan kirimkan password")).message_id)
        await state.set_state(GuestStates.register_2_edit_password)
    
    elif edit_type == "bank":
        builder = keyboard_guest.bank_selection(register_model.bank_list, show_cancel=False)
        register_model.add_message_id((await callback.message.answer("Silahkan pilih bank", reply_markup=builder.as_markup())).message_id)
        await state.set_state(GuestStates.register_3_edit_bank_name)
    
    elif edit_type == "bank_account_name":
        register_model.add_message_id((await callback.message.answer("Silahkan kirimkan nama rekening")).message_id)
        await state.set_state(GuestStates.register_4_edit_bank_account_name)
    
    elif edit_type == "bank_account_number":
        register_model.add_message_id((await callback.message.answer("Silahkan kirimkan nomor rekening")).message_id)
        await state.set_state(GuestStates.register_5_edit_bank_account_number)

    elif edit_type == "referral_code":
        register_model.add_message_id((await callback.message.answer("Silahkan kirimkan referral code")).message_id)
        await state.set_state(GuestStates.register_6_edit_referral_code)
    return
