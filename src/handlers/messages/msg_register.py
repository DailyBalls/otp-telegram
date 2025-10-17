from aiogram import Router, types
from aiogram.types.contact import Contact
from aiogram.fsm.context import FSMContext
from aiogram.types.inline_keyboard_button import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import BotConfig
from models.model_register import ModelRegister
import utils.validators as validators
from bot_instance import GuestStates
from keyboards.inline import keyboard_guest

async def msg_register_1_username(msg: types.Message, config: BotConfig, state: FSMContext, register_model: ModelRegister) -> None:
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
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="Batalkan", callback_data="register_cancel"))
        register_model.add_message_id((await msg.answer("Silahkan kirimkan password", reply_markup=builder.as_markup())).message_id)
        await state.set_state(GuestStates.register_2_ask_password)

    elif current_state == GuestStates.register_1_edit_username:
        # register_model.add_message_id((await msg.answer("Username berhasil dirubah")).message_id)
        await state.set_state(GuestStates.register_6_ask_confirm_register)
        register_model.add_message_id((await send_confirmation_register_message(msg, register_model)).message_id)

    return


async def msg_register_2_password(msg: types.Message, config: BotConfig, state: FSMContext, register_model: ModelRegister) -> None:
    if not validators.min_length(msg.text, 6):
        builder = InlineKeyboardBuilder()
        register_model.add_message_id((await msg.answer("Password harus minimal 6 karakter")).message_id)
        return

    register_model.set_password(msg.text)

    current_state = await state.get_state()
    if current_state == GuestStates.register_2_ask_password:
        # register_model.add_message_id((await msg.answer("Password berhasil diterima")).message_id)
        await state.set_state(GuestStates.register_3_ask_bank_name)
        builder = keyboard_guest.bank_selection(register_model.bank_list)
        register_model.add_message_id((await msg.answer("Silahkan pilih bank yang ingin Anda gunakan", reply_markup=builder.as_markup())).message_id)

    elif current_state == GuestStates.register_2_edit_password:
        await state.set_state(GuestStates.register_6_ask_confirm_register)
        register_model.add_message_id((await send_confirmation_register_message(msg, register_model)).message_id)

    return
        

# Handle if user send bank name through message
async def msg_register_3_bank_name(msg: types.Message, config: BotConfig, state: FSMContext, register_model: ModelRegister) -> None:
    register_model.set_bank_name(msg.text)
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Batalkan", callback_data="register_cancel"))

    current_state = await state.get_state()
    if current_state == GuestStates.register_3_ask_bank_name:
        register_model.add_message_id((await msg.answer(f"Bank <b>{register_model.bank_name}</b> berhasil dipilih")).message_id)
        register_model.add_message_id((await msg.answer("Silahkan kirimkan nama rekening", reply_markup=builder.as_markup())).message_id)
        await state.set_state(GuestStates.register_4_ask_bank_account_name)
    elif current_state == GuestStates.register_3_edit_bank_name:
        register_model.add_message_id((await msg.answer(f"Bank <b>{register_model.bank_name}</b> berhasil dirubah")).message_id)
        register_model.add_message_id((await send_confirmation_register_message(msg, register_model)).message_id)
        await state.set_state(GuestStates.register_6_ask_confirm_register)

    await state.set_state(GuestStates.register_4_ask_bank_account_name)
    return


async def msg_register_4_bank_account_name(msg: types.Message, config: BotConfig, state: FSMContext, register_model: ModelRegister) -> None:
    # Check that the input name contains only letters (including Unicode letters) and spaces
    if not msg.text or not validators.alpha_space(msg.text):
        register_model.add_message_id((await msg.answer("Nama rekening hanya boleh berisi huruf dan spasi. Silakan kirimkan nama rekening yang valid.")).message_id)
        return
    if not validators.min_length(msg.text, 5):
        register_model.add_message_id((await msg.answer("Nama rekening harus minimal 5 karakter")).message_id)
        return

    register_model.set_bank_account_name(msg.text)
    
    current_state = await state.get_state()
    if current_state == GuestStates.register_4_ask_bank_account_name:
        # register_model.add_message_id((await msg.answer("Nama rekening berhasil diterima")).message_id)
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="Batalkan", callback_data="register_cancel"))
        register_model.add_message_id((await msg.answer("Silahkan kirimkan nomor rekening", reply_markup=builder.as_markup())).message_id)
        await state.set_state(GuestStates.register_5_ask_bank_account_number)
    elif current_state == GuestStates.register_4_edit_bank_account_name:
        # register_model.add_message_id((await msg.answer("Nama rekening berhasil dirubah")).message_id)
        await state.set_state(GuestStates.register_6_ask_confirm_register)
        register_model.add_message_id((await send_confirmation_register_message(msg, register_model)).message_id)

    return


async def msg_register_5_bank_account_number(msg: types.Message, config: BotConfig, state: FSMContext, register_model: ModelRegister) -> None:

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
        await state.set_state(GuestStates.register_6_ask_confirm_register)

    elif current_state == GuestStates.register_5_edit_bank_account_number:
        # register_model.add_message_id((await msg.answer("Nomor rekening berhasil dirubah")).message_id)
        await state.set_state(GuestStates.register_6_ask_confirm_register)
    
    register_model.add_message_id((await send_confirmation_register_message(msg, register_model)).message_id)

    return


async def send_confirmation_register_message(msg: types.Message, register_model: ModelRegister):
    register_username = register_model.username
    register_password = register_model.password
    register_bank_name = register_model.bank_name
    register_bank_account_name = register_model.bank_account_name
    register_bank_account_number = register_model.bank_account_number

    builder_confirm = keyboard_guest.registration_confirm_and_edit()
    return await msg.answer(f"""
<b>Konfirmasi Register</b>
Username: <b>{register_username}</b>
Password: <b>{register_password}</b>
Bank: <b>{register_bank_name}</b>
Nama Rekening: <b>{register_bank_account_name}</b>
Nomor Rekening: <b>{register_bank_account_number}</b>

Apakah data yang Anda kirimkan sudah benar?
""", reply_markup=builder_confirm.as_markup())
