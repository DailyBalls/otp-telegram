from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot_instance import GuestStates, bot, LoggedInStates
from config import BotConfig
from handlers.callbacks.callback_auth import callback_auth_clear
from handlers.messages.msg_register import send_confirmation_register_message
from handlers.multi import multi_menu
from handlers.multi.multi_authentication import get_logged_in_menu_builder
from keyboards.inline import keyboard_guest
from models.model_register import ModelRegister
from models.model_telegram_data import ModelTelegramData
from models.model_user import ModelUser
from services.otp_services.api_client import OTPAPIClient
import utils.models as model_utils

async def callback_register_edit(callback: types.CallbackQuery, config: BotConfig, state: FSMContext, register_model: ModelRegister) -> None:
    current_state = await state.get_state()
    # Only allow this callback if the current state is register_6_ask_confirm_register
    if(current_state != GuestStates.register_6_ask_confirm_register):
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
    return

async def callback_register_bank(callback: types.CallbackQuery, config: BotConfig, state: FSMContext, register_model: ModelRegister) -> None:
    current_state = await state.get_state()

    if current_state != GuestStates.register_3_ask_bank_name and current_state != GuestStates.register_3_edit_bank_name:
        return

    # Check if register data is valid
    register_bank_name = callback.data.replace("register_bank_", "")
    if register_model.bank_list is not None and register_bank_name not in register_model.bank_list:
        await callback.answer(f"Bank {register_bank_name} tidak valid")
        return
    
    register_model.set_bank_name(register_bank_name)
    
    current_state = await state.get_state()
    await callback.message.edit_reply_markup(reply_markup=None)
    register_model.add_message_id((await callback.message.answer(f"Bank <b>{register_bank_name}</b> berhasil dipilih")).message_id)
    if current_state == GuestStates.register_3_ask_bank_name:
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(text="❌ Batalkan", callback_data="register_cancel"))
        register_model.add_message_id((await callback.message.answer("Silahkan kirimkan nama rekening", reply_markup=builder.as_markup())).message_id)
        await state.set_state(GuestStates.register_4_ask_bank_account_name)
    elif current_state == GuestStates.register_3_edit_bank_name:
        register_model.add_message_id((await send_confirmation_register_message(callback.message, register_model)).message_id)
        await state.set_state(GuestStates.register_6_ask_confirm_register)
    await register_model.save_to_state()
    return

async def callback_register_confirm_yes(callback: types.CallbackQuery, config: BotConfig, state: FSMContext, register_model: ModelRegister) -> None:
    api_client = OTPAPIClient(state=state, user_id=callback.from_user.id, base_url=config.otp_host)
    submit_registration = await api_client.submit_registration(register_model.get_submit_registration_data())
    if submit_registration.is_error:
        await callback.answer(f"Gagal melakukan registrasi")
        if submit_registration.has_validation_errors:
            for field, errors in submit_registration.metadata.get('validation', {}).items():
                for error in errors:
                    register_model.add_message_id((await callback.message.answer(f"Validasi Error: {error}")).message_id)
        print("There is an error when submitting registration to OTP API", submit_registration.error, submit_registration.metadata)
        return
    await register_model.delete_all_messages()

    await state.update_data(**{register_model._get_state_key(): None}) # Delete the register model from the state
    user_model = ModelUser(
        **submit_registration.data,
        state=state,
        chat_id=callback.message.chat.id,
        is_authenticated=True,
    )
    await user_model.save_to_state()
    user_model.add_message_id((await callback.message.answer("Berhasil melakukan registrasi", reply_markup=get_logged_in_menu_builder().as_markup(resize_keyboard=True))).message_id)
    await callback.answer("Registrasi berhasil")
    await callback_auth_clear(config, state)

    # Redirect to authenticated /start command
    await state.set_state(LoggedInStates.main_menu)
    await multi_menu.logged_in_menu(callback.message, config, state, user_model)
    return

async def callback_register_confirm_no(callback: types.CallbackQuery, config: BotConfig, state: FSMContext, register_model: ModelRegister) -> None:
    await callback.answer("Register dibatalkan")
    await register_model.delete_all_messages()
    await state.update_data(register=None)
    await callback_auth_clear(config, state)
    return
