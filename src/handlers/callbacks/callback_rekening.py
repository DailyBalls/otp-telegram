from typing import List
from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.types.inline_keyboard_button import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import BotConfig
from models.model_rekening import Rekening
from services.otp_services.api_client import OTPAPIClient
from models.model_user import ModelUser

async def callback_rekening_list(callback: types.CallbackQuery, config: BotConfig, state: FSMContext, api_client: OTPAPIClient, user_model: ModelUser) -> None:
    rekening = await api_client.list_rekening()
    if rekening.is_error:
        await callback.answer("Gagal memuat daftar rekening")
        return
    
    rekening_list: List[Rekening] = []
    for rekening in rekening.data:
        rekening_list.append(Rekening(**rekening))
    
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Tambahkan Rekening", callback_data=f"rekening_add"))
    builder.adjust(1)
    
    reply_message = f"""
Menampilkan daftar rekening yang anda miliki
"""
    for rekening in rekening_list:
        reply_message += f""" {"<b>" if rekening.default else ""}
Bank: {rekening.bank_name} {"(Default)" if rekening.default else ""}
Nama Rekening: {rekening.bank_account_name}
Nomor Rekening: {rekening.bank_account_number}
Rekening Withdraw: {"Ya" if rekening.default else "Tidak"}
{"</b>" if rekening.default else ""}"""

    reply_message += f"""

Untuk perubahan Rekening Withdraw, silahkan chat customer service kami
"""
    user_model.add_message_id((await callback.message.answer(reply_message, reply_markup=builder.as_markup())).message_id)
    await user_model.save_to_state()
    return