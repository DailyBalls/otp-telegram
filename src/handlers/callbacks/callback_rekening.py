from contextlib import suppress
from typing import List
from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.types.callback_query import CallbackQuery
from aiogram.types.inline_keyboard_button import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot_instance import LoggedInStates, bot
from config import BotConfig
from models.model_rekening import Rekening
from services.otp_services.api_client import OTPAPIClient
from models.model_user import ModelUser, RekeningAdd
from services.otp_services.models import APIResponse

async def callback_rekening_list(callback: CallbackQuery, config: BotConfig, state: FSMContext, api_client: OTPAPIClient, user_model: ModelUser) -> None:
    rekening = await api_client.list_rekening()
    if rekening.is_error:
        await callback.answer("Gagal memuat daftar rekening")
        return
    
    rekening_list: List[Rekening] = []
    for rekening in rekening.data:
        rekening_list.append(Rekening(**rekening))
    
    builder = InlineKeyboardBuilder()
    if user_model.is_active():
        builder.add(InlineKeyboardButton(text="Tambahkan Rekening", callback_data=f"rekening_add"))
    builder.add(InlineKeyboardButton(text="Tutup", callback_data="action_close_with_answer_"))
    builder.adjust(2)
    
    reply_message = f"""
Menampilkan daftar rekening yang anda miliki
"""
    for rekening in rekening_list:
        reply_message += f""" {"<b>" if rekening.default else ""}
Bank: <code>{rekening.bank_name}</code> {"(Default)" if rekening.default else ""}
Nama Rekening: <code>{rekening.bank_account_name}</code>
Nomor Rekening: <code>{rekening.bank_account_number}</code>
Rekening Withdraw: {"Ya" if rekening.default else "Tidak"}
{"</b>" if rekening.default else ""}"""

    reply_message += f"""

Untuk perubahan Rekening Withdraw, silahkan chat customer service kami
"""
    user_model.add_message_id((await callback.message.answer(reply_message, reply_markup=builder.as_markup())).message_id)
    await user_model.save_to_state()
    return

async def callback_rekening_add(callback: CallbackQuery, config: BotConfig, state: FSMContext, api_client: OTPAPIClient, user_model: ModelUser) -> None:
    api_initiate_rekening_add = await api_client.initiate_rekening_add()
    if api_initiate_rekening_add.is_error:
        await callback.answer("Gagal memuat daftar bank")
        return
    
    await state.set_state(LoggedInStates.rekening_add_1_ask_bank_name)
    
    if user_model.temp_rekening_add is not None and user_model.temp_rekening_add.list_messages_ids is not None:
        with suppress(Exception):
            await bot.delete_messages(user_model.chat_id, user_model.temp_rekening_add.list_messages_ids)

    user_model.temp_rekening_add = RekeningAdd(
        initiator_message_id=callback.message.message_id,
        list_active_banks=api_initiate_rekening_add.data.get("bankList", []),
        list_user_banks=api_initiate_rekening_add.data.get("userBankList", []),
        bank_name=None,
        bank_account_name=None,
        bank_account_number=None,
        list_messages_ids=[],
    )
    
    await callback.answer()
    builder = InlineKeyboardBuilder()
    for bank in user_model.temp_rekening_add.list_active_banks:
        builder.add(InlineKeyboardButton(text=bank, callback_data=f"rekening_add_bank_{bank}"))
    builder.adjust(2)
   
    user_model.add_rekening_message_id((await callback.message.answer("Silahkan pilih bank yang ingin anda tambahkan", reply_markup=builder.as_markup())).message_id)
    await user_model.save_to_state()
    return

async def callback_rekening_add_bank(callback: CallbackQuery, config: BotConfig, state: FSMContext, user_model: ModelUser) -> None:
    bank_name = callback.data.replace("rekening_add_bank_", "")
    if user_model.temp_rekening_add.list_active_banks is not None and bank_name not in user_model.temp_rekening_add.list_active_banks:
        await callback.answer(f"Bank {bank_name} tidak valid")
        return
    
    if user_model.temp_rekening_add.list_user_banks is not None and bank_name in user_model.temp_rekening_add.list_user_banks:
        await callback.answer(f"Bank {bank_name} sudah terdaftar sebagai rekening anda")
        return
    
    await state.set_state(LoggedInStates.rekening_add_2_ask_bank_account_name)
    user_model.temp_rekening_add.bank_name = bank_name

    await callback.message.edit_text(f"Bank <b>{bank_name}</b> berhasil dipilih", reply_markup=None)
    await callback.answer(f"{bank_name} berhasil dipilih")
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="❌ Batalkan", callback_data="rekening_add_cancel"))
    
    user_model.add_rekening_message_id((await callback.message.answer("Silahkan kirimkan nama rekening", reply_markup=builder.as_markup())).message_id)
    await user_model.save_to_state()
    return

async def callback_rekening_add_cancel(callback: CallbackQuery, config: BotConfig, state: FSMContext, user_model: ModelUser) -> None:
    await state.set_state(None)
    if user_model.temp_rekening_add is not None and user_model.temp_rekening_add.list_messages_ids is not None:
        with suppress(Exception):
            await bot.delete_messages(user_model.chat_id, user_model.temp_rekening_add.list_messages_ids)
    user_model.temp_rekening_add = None
    await callback.answer("Penambahan rekening dibatalkan")
    return

async def callback_rekening_add_confirm(callback: CallbackQuery, config: BotConfig, state: FSMContext, api_client: OTPAPIClient, user_model: ModelUser) -> None:
    api_insert_rekening: APIResponse = await api_client.insert_rekening(user_model.temp_rekening_add.bank_name, user_model.temp_rekening_add.bank_account_name, user_model.temp_rekening_add.bank_account_number)
    if api_insert_rekening.is_error:
        await callback.answer(f"Gagal menambahkan rekening")
        return
    
    if user_model.temp_rekening_add is not None and user_model.temp_rekening_add.list_messages_ids is not None:
        with suppress(Exception):
            await bot.delete_messages(user_model.chat_id, user_model.temp_rekening_add.list_messages_ids)
    if user_model.temp_rekening_add.initiator_message_id is not None:
        with suppress(Exception):
            await bot.delete_message(user_model.chat_id, user_model.temp_rekening_add.initiator_message_id)
    
    await state.set_state(None)
    user_model.temp_rekening_add = None
    await callback.answer("Rekening berhasil ditambahkan")
    return await callback_rekening_list(callback, config, state, api_client, user_model)