from aiogram import types
from aiogram.fsm.context import FSMContext
from config import BotConfig
from models.model_user import ModelUser
import utils.validators as validators
from bot_instance import LoggedInStates
from aiogram.types.inline_keyboard_button import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

async def msg_rekening_ask_bank_account_name(msg: types.Message, config: BotConfig, state: FSMContext, user_model: ModelUser) -> None:
    user_model.add_rekening_message_id(msg.message_id)
    if msg.text is None or not validators.alpha_space(msg.text):
        user_model.add_rekening_message_id((await msg.answer("Nama rekening hanya boleh berisi huruf dan spasi. Silakan kirimkan nama rekening yang valid.")).message_id)
        await user_model.save_to_state()
        return
    if not validators.min_length(msg.text, 5):
        user_model.add_rekening_message_id((await msg.answer("Nama rekening harus minimal 5 karakter")).message_id)
        await user_model.save_to_state()
        return
    user_model.temp_rekening_add.bank_account_name = msg.text

    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Batalkan", callback_data="rekening_add_cancel"))

    user_model.add_rekening_message_id((await msg.answer("Silahkan kirimkan nomor rekening", reply_markup=builder.as_markup())).message_id)
    await state.set_state(LoggedInStates.rekening_add_3_ask_bank_account_number)
    await user_model.save_to_state()
    return

async def msg_rekening_ask_bank_account_number(msg: types.Message, config: BotConfig, state: FSMContext, user_model: ModelUser) -> None:
    user_model.add_rekening_message_id(msg.message_id)
    if msg.text is None or not validators.numeric(msg.text):
        user_model.add_rekening_message_id((await msg.answer("Nomor rekening harus berupa angka")).message_id)
        await user_model.save_to_state()
        return
    if not validators.min_length(msg.text, 8):
        user_model.add_rekening_message_id((await msg.answer("Nomor rekening harus minimal 8 digit")).message_id)
        await user_model.save_to_state()
        return
    user_model.temp_rekening_add.bank_account_number = msg.text
    await state.set_state(LoggedInStates.rekening_add_4_ask_confirm_add)

    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Batalkan", callback_data="rekening_add_cancel"))
    builder.add(InlineKeyboardButton(text="Konfirmasi", callback_data="rekening_add_confirm"))
    builder.adjust(2)
    user_model.add_rekening_message_id((await msg.answer(f"""
<b>Konfirmasi Data Rekening</b>
Bank: <code>{user_model.temp_rekening_add.bank_name}</code>
Nama Rekening: <code>{user_model.temp_rekening_add.bank_account_name}</code>
Nomor Rekening: <code>{user_model.temp_rekening_add.bank_account_number}</code>

Apakah data yang Anda kirimkan sudah benar? Jika sudah benar, silahkan klik tombol <b>"Konfirmasi"</b> untuk menyimpan data rekening.
""", reply_markup=builder.as_markup())).message_id)
    await user_model.save_to_state()
    return