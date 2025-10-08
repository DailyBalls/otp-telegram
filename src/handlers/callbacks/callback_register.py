from aiogram import types
from aiogram.fsm.context import FSMContext

from bot_instance import GuestStates, bot
from config import BotConfig
from handlers.messages.msg_register import send_confirmation_register_message
from keyboards.inline import keyboard_register
from models.model_register import ModelRegister
from services.otp_services.api_client import OTPAPIClient

async def callback_register_init(callback: types.CallbackQuery, config: BotConfig, state: FSMContext) -> None:    # Check if register data is valid
    cancel_builder = keyboard_register.register_cancel()
    fsm_data = await state.get_data()
    register_data = fsm_data.get("register", False)
    if register_data:
        register_model = ModelRegister.model_validate_json(register_data)
        await register_model.delete_all_messages()
        await state.update_data(register=None)

    api_client = OTPAPIClient(state=state, user_id=callback.from_user.id, base_url=config.otp_host)
    ask_auth = await api_client.ask_auth()
    if ask_auth.is_error:
        await callback.answer(f"Gagal memulai proses register")
        print("There is an error when asking for auth to OTP API", ask_auth.error)
        return
 
    await callback.answer("Memulai proses register...")
    register_model = ModelRegister(state=state)
    register_model.set_chat_id(callback.message.chat.id)
    register_model.set_bank_list(ask_auth.data.get("bank_list", []))
    register_model.set_is_required_captcha(ask_auth.data.get("captcha", False))
    register_model.set_phone_number(fsm_data.get("contact_phone", None))
    register_model.add_message_id((await callback.message.answer("Silahkan kirimkan username", reply_markup=cancel_builder.as_markup())).message_id)
    await state.set_state(GuestStates.register_1_ask_username)

async def callback_register_cancel(callback: types.CallbackQuery, config: BotConfig, state: FSMContext, register_model: ModelRegister = None) -> None:
    await callback.answer("Register dibatalkan")
    await bot.delete_message(callback.message.chat.id, callback.message.message_id)
    if register_model is not None:
        await register_model.delete_all_messages()
        return
    await state.update_data(register=None)
    return

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
        builder = keyboard_register.bank_selection(register_model.bank_list)
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
    cancel_builder = keyboard_register.register_cancel()
    current_state = await state.get_state()

    if current_state != GuestStates.register_3_ask_bank_name and current_state != GuestStates.register_3_edit_bank_name:
        return

    # Check if register data is valid
    register_bank_name = callback.data.replace("register_bank_", "")
    if(register_bank_name.lower() == "other"):
        await callback.answer(f"Bank {register_bank_name} tidak aktif")
        return
    
    register_model.set_bank_name(register_bank_name)
    
    current_state = await state.get_state()
    if current_state == GuestStates.register_3_ask_bank_name:
        register_model.add_message_id((await callback.message.answer(f"Bank <b>{register_bank_name}</b> berhasil dipilih")).message_id)
        register_model.add_message_id((await callback.message.answer("Silahkan kirimkan nama rekening", reply_markup=cancel_builder.as_markup())).message_id)
        await state.set_state(GuestStates.register_4_ask_bank_account_name)
    elif current_state == GuestStates.register_3_edit_bank_name:
        register_model.add_message_id((await callback.message.answer(f"Bank <b>{register_bank_name}</b> berhasil dirubah")).message_id)
        register_model.add_message_id((await send_confirmation_register_message(callback.message, register_model)).message_id)
        await state.set_state(GuestStates.register_6_ask_confirm_register)

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
    await state.update_data(register=None)
    await callback.message.answer("Berhasil melakukan registrasi")
    await callback.answer("Registrasi berhasil")
    # await callback_register_execute(callback, config, state, register_model)
    return

async def callback_register_confirm_no(callback: types.CallbackQuery, config: BotConfig, state: FSMContext, register_model: ModelRegister) -> None:
    await callback.answer("Register dibatalkan")
    await register_model.delete_all_messages()
    await state.update_data(register=None)
    return
