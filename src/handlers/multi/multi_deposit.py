from typing import List, Optional
from aiogram.types import InlineKeyboardButton
from aiogram.types.callback_query import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.types.message import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from pydantic import BaseModel
from bot_instance import LoggedInStates, bot
from config import BotConfig
from models.model_telegram_data import ModelTelegramData
from models.model_user import ModelUser
from services.otp_services.api_client import OTPAPIClient
import utils.models as model_utils
import re
import unicodedata
ACTION_DEPOSIT = "deposit"
KEY_CACHED_DEPOSIT_AMOUNTS = "cached_deposit_amounts"
ACTION_DATA_MINIMUM_DEPOSIT = "minimum_deposit"
ACTION_DATA_MAXIMUM_DEPOSIT = "maximum_deposit"
ACTION_DATA_USER_BANKS = "user_banks"
ACTION_DATA_DEPOSIT_BANKS = "deposit_banks"
ACTION_DATA_QRIS_PAYMENT_GATEWAY = "qris_payment_gateway"
ACTION_DATA_VA_PAYMENT_GATEWAY = "va_payment_gateway"
ACTION_DATA_PROMO = "promo"
ACTION_DATA_MINIMUM_DEPOSIT_PROMO = "minimum_deposit_promo"

ACTION_SUBMITTED_DEPOSIT_METHOD = "submitted_deposit_method"
ACTION_SUBMITTED_DEPOSIT_CHANNEL_ID = "submitted_deposit_channel_id"
ACTION_SUBMITTED_DEPOSIT_AMOUNT = "submitted_deposit_amount"
ACTION_SUBMITTED_USER_BANK = "submitted_user_bank"
ACTION_SUBMITTED_PROMO = "submitted_promo"
ACTION_SUBMITTED_NOTE = "submitted_note"
BANK_STATUS_OFFLINE = 0
BANK_STATUS_ONLINE = 1
BANK_STATUS_MAINTENANCE = 2

MESSAGE_MENU_DEPOSIT_METHOD = "menu_deposit_method"
MESSAGE_MENU_DEPOSIT_CHANNEL = "menu_deposit_channel"
MESSAGE_MENU_DEPOSIT_USER_BANK = "menu_deposit_user_bank"
MESSAGE_MENU_DEPOSIT_PROMO = "menu_deposit_promo"
MESSAGE_MENU_DEPOSIT_CONFIRM_PROMO = "menu_deposit_confirm_promo"
MESSAGE_MENU_DEPOSIT_NOTE = "menu_deposit_note"
MESSAGE_MENU_DEPOSIT_AMOUNT = "menu_deposit_amount"

KETENTUAN_DEPOSIT = """
<b>Ketentuan Deposit :</b>
Mohon perhatikan Nomor Rekening Tujuan yang tersedia.

<b>Kami tidak memberikan toleransi apabila terjadi kesalahan deposit ke Nomor Rekening Tujuan yang bukan milik/tertera di website kami.</b>

Catatan :
- Harap melakukan konfirmasi Deposit satu kali saja
- Tunggu hingga permohonan anda diproses oleh staf kami
- Saldo akan bertambah otomatis jika sudah diproses
"""

'''
Deposit init function

Entrypoint:
- Callback Button (data: menu_deposit)
- Message Router (text: deposit)
- Command Router (cmd: deposit)
'''

class UserBank(BaseModel):
    id: Optional[int] = None
    bank_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_account_name: Optional[str] = None
    is_default: Optional[bool] = None

class DepositBank(BaseModel):
    id: Optional[int] = None
    bank_name: Optional[str] = None
    bank_account_display: Optional[str] = None
    bank_status: Optional[int] = None
    bank_account_number: Optional[str] = None
    bank_account_name: Optional[str] = None

class PaymentGateway(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    type: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None

'''
Deposit Init Function

Entrypoint:
- Callback Button (data: menu_deposit)
- Message Router (text: deposit)
- Command Router (cmd: deposit)
'''
async def deposit_init(event: Message | CallbackQuery, config: BotConfig, state: FSMContext, user_model: ModelUser, chat_id: int, api_client: OTPAPIClient, telegram_data: ModelTelegramData) -> None:
    if user_model.action is not None:
        await user_model.await_finish_action()
    
    response = await api_client.initiate_deposit()
    if response.is_error:
        error_message = f"❌ Gagal memulai proses deposit\nError: {response.get_error_message()}"
        if isinstance(event, CallbackQuery):
            await event.answer()
            await event.message.answer(error_message)
        elif isinstance(event, Message):
            await event.answer(error_message)
        return
    
    if response.data.get("pending_deposit", False) == True:
        await event.answer("Masih ada Deposit yang sedang berlangsung")
        return

    bank_data = response.data.get("bank", None)
    user_banks: list[UserBank] = []
    deposit_banks: list[DepositBank] = []

    if bank_data is not None:
        for bank in bank_data.get("user_rekening", []):
            user_banks.append(UserBank(**bank))
        for bank in bank_data.get("rekening_tujuan", []):
            deposit_banks.append(DepositBank(**bank))

    payment_gateway_data = response.data.get("payment_gateway", None)

    qris_payment_gateway: List[PaymentGateway] = []
    for payment_gateway in payment_gateway_data.get("QRIS", []):
        qris_payment_gateway.append(PaymentGateway(**payment_gateway))

    va_payment_gateway: List[PaymentGateway] = []
    for payment_gateway in payment_gateway_data.get("VA", []):
        va_payment_gateway.append(PaymentGateway(**payment_gateway))

    user_model.initiate_action(ACTION_DEPOSIT)
    user_model.action.set_action_data(ACTION_DATA_MINIMUM_DEPOSIT, int(response.data.get("min_deposit")))
    user_model.action.set_action_data(ACTION_DATA_MAXIMUM_DEPOSIT, int(response.data.get("max_deposit")))
    user_model.action.set_action_data(ACTION_DATA_USER_BANKS, user_banks)
    user_model.action.set_action_data(ACTION_DATA_DEPOSIT_BANKS, deposit_banks)
    user_model.action.set_action_data(ACTION_DATA_QRIS_PAYMENT_GATEWAY, qris_payment_gateway)
    user_model.action.set_action_data(ACTION_DATA_VA_PAYMENT_GATEWAY, va_payment_gateway)
    user_model.action.set_action_data(ACTION_DATA_PROMO, response.data.get("list_promo_event", []))


    if isinstance(event, CallbackQuery):
        await event.answer()
    
    user_model.add_action_message_id((await bot.send_message(chat_id, KETENTUAN_DEPOSIT)).message_id)
    
    await user_model.save_to_state()
    return await deposit_ask_method(event, config, state, user_model, chat_id)

'''
Deposit Ask Method Function

Entrypoint:
- Init Function (deposit_init) (CallbackQuery | Message)
'''
async def deposit_ask_method(event: CallbackQuery | Message, config: BotConfig, state: FSMContext, user_model: ModelUser, chat_id: int) -> None:
    if user_model.action is None or user_model.action.current_action != ACTION_DEPOSIT:
        if isinstance(event, CallbackQuery):
            await event.message.answer("Aksi tidak valid, silahkan ulangi proses deposit", reply_markup=None)
            await event.answer()
        elif isinstance(event, Message):
            await event.answer("Aksi tidak valid, silahkan ulangi proses deposit")
        return

    builder = InlineKeyboardBuilder()
    
    deposit_banks = user_model.action.get_action_data(ACTION_DATA_DEPOSIT_BANKS)
    qris_payment_gateway = user_model.action.get_action_data(ACTION_DATA_QRIS_PAYMENT_GATEWAY)
    va_payment_gateway = user_model.action.get_action_data(ACTION_DATA_VA_PAYMENT_GATEWAY)

    if deposit_banks is not None and len(deposit_banks) > 0:
        builder.add(InlineKeyboardButton(text="Bank", callback_data=f"deposit_submit_method_BANK"))
    if qris_payment_gateway is not None and len(qris_payment_gateway) > 0:
        builder.add(InlineKeyboardButton(text="QRIS", callback_data=f"deposit_submit_method_QRIS"))
    if va_payment_gateway is not None and len(va_payment_gateway) > 0:
        builder.add(InlineKeyboardButton(text="Virtual Account", callback_data=f"deposit_submit_method_VA"))
    builder.add(InlineKeyboardButton(text="❌ Batalkan", callback_data="deposit_cancel"))
    builder.adjust(1)
    message = f"Pilih metode pembayaran untuk melakukan deposit"
    method_message_id = user_model.action.get_action_data(MESSAGE_MENU_DEPOSIT_METHOD)
    print("Method Message ID: ", method_message_id)
    if method_message_id is not None:
        await bot.edit_message_text(chat_id=chat_id, message_id=method_message_id, text=message, reply_markup=builder.as_markup())
    else:
        if isinstance(event, CallbackQuery):
            await event.answer()
            method_message_id = (await event.message.answer(message, reply_markup=builder.as_markup())).message_id
        elif isinstance(event, Message):
            method_message_id = (await event.answer(message, reply_markup=builder.as_markup())).message_id
        user_model.add_action_message_id(method_message_id)
        user_model.action.set_action_data(MESSAGE_MENU_DEPOSIT_METHOD, method_message_id)
    await state.set_state(LoggedInStates.deposit_ask_method)
    await user_model.save_to_state()
    return

async def deposit_submit_method(event: CallbackQuery, config: BotConfig, state: FSMContext, user_model: ModelUser, chat_id: int) -> None:
    if user_model.action is None or user_model.action.current_action != ACTION_DEPOSIT:
        await event.message.edit_text("Aksi tidak valid, silahkan ulangi proses deposit", reply_markup=None)
        await event.answer()
        return
    
    route = event.data.replace("deposit_submit_method_", "").split("_")
    method = route[0]
    if method not in ["BANK", "QRIS", "VA"]:
        await event.answer("Metode pembayaran tidak valid")
        return
    
    user_model.action.set_action_data(ACTION_SUBMITTED_DEPOSIT_METHOD, method)
    await event.message.edit_text(text=f"Terpilih metode pembayaran: <b>{method}</b>", reply_markup=None)
    await user_model.save_to_state()
    return await deposit_ask_channel(event, config, state, user_model, chat_id, method)
    
'''
Deposit Ask Channel Function

Entrypoint:
- Callback Button (data: deposit_ask_channel)
- Deposit Submit Method Function (deposit_submit_method)
'''
async def deposit_ask_channel(event: CallbackQuery, config: BotConfig, state: FSMContext, user_model: ModelUser, chat_id: int, method: str = None) -> None:
    if user_model.action is None or user_model.action.current_action != ACTION_DEPOSIT:
        await event.message.edit_text("Aksi tidak valid, silahkan ulangi proses deposit", reply_markup=None)
        await event.answer()
        return

    if method is None:
        method = user_model.action.get_action_data(ACTION_SUBMITTED_DEPOSIT_METHOD)
        if method is None:
            await event.answer("Aksi tidak valid, silahkan ulangi proses deposit")
            return
    
    builder = InlineKeyboardBuilder()
    message = ""

    if method == "BANK":
        deposit_banks = user_model.action.get_action_data(ACTION_DATA_DEPOSIT_BANKS)
        message = "Silahkan pilih rekening deposit untuk melakukan pembayaran"
        for bank in deposit_banks:
            builder.add(InlineKeyboardButton(text=f"{bank['bank_account_display']}", callback_data=f"deposit_channel_BANK_{bank['id']}"))
        builder.adjust(1)
    
    elif method == "QRIS":
        qris_payment_gateway = user_model.action.get_action_data(ACTION_DATA_QRIS_PAYMENT_GATEWAY)
        message = "Silahkan pilih payment gateway untuk pembayaran via QRIS"
        for payment_gateway in qris_payment_gateway:
            builder.add(InlineKeyboardButton(text=f"{payment_gateway['type']} - {payment_gateway['name']}", callback_data=f"deposit_channel_QRIS_{payment_gateway['id']}"))
        builder.adjust(1)
    
    elif method == "VA":
        virtual_account_payment_gateway = user_model.action.get_action_data(ACTION_DATA_VA_PAYMENT_GATEWAY)
        message = "Silahkan pilih payment gateway untuk pembayaran via Virtual Account"
        for payment_gateway in virtual_account_payment_gateway:
            builder.add(InlineKeyboardButton(text=f"{payment_gateway['code']} {payment_gateway['type']} - {payment_gateway['name']}", callback_data=f"deposit_channel_VA_{payment_gateway['id']}"))
        builder.adjust(1)
    
    navigation_builder = InlineKeyboardBuilder()
    navigation_builder.add(InlineKeyboardButton(text="🔙 Kembali", callback_data="deposit_back_button_ask_method"))
    navigation_builder.add(InlineKeyboardButton(text="❌ Batalkan", callback_data="deposit_cancel"))
    navigation_builder.adjust(2)
    builder.attach(navigation_builder)
    message_id = user_model.action.get_action_data(MESSAGE_MENU_DEPOSIT_CHANNEL)
    if message_id is not None:
        await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=message, reply_markup=builder.as_markup())
    else:
        message_id = (await event.message.answer(message, reply_markup=builder.as_markup())).message_id
        user_model.add_action_message_id(message_id)
        user_model.action.set_action_data(MESSAGE_MENU_DEPOSIT_CHANNEL, message_id)
    await user_model.save_to_state()
    await event.answer()
    return

'''
Deposit Channel Function

Entrypoint:
- Callback Button (data: deposit_channel_{method}_{channel_id})
'''
async def deposit_channel(event: CallbackQuery, config: BotConfig, state: FSMContext, user_model: ModelUser, chat_id: int) -> None:
    if user_model.action is None or user_model.action.current_action != ACTION_DEPOSIT:
        await event.message.edit_text("Aksi tidak valid, silahkan ulangi proses deposit", reply_markup=None)
        await event.answer()
        return
    
    data = event.data.replace("deposit_channel_", "").split("_")
    try:
        method = data[0]
        channel_id = int(data[1])
    except:
        await event.answer("Metode pembayaran tidak valid")
        return
    if method not in ["BANK", "QRIS", "VA"]:
        await event.answer("Metode pembayaran tidak valid")
        return
    
    if method == "BANK":
        bank = next((bank for bank in user_model.action.get_action_data(ACTION_DATA_DEPOSIT_BANKS) if bank["id"] == channel_id), None)
        if bank is None:
            await event.answer("Bank tidak valid")
            return
        elif bank['bank_status'] == BANK_STATUS_OFFLINE:
            await event.answer("Bank sedang offline")
            return
        elif bank['bank_status'] == BANK_STATUS_MAINTENANCE:
            await event.answer("Bank sedang gangguan")
            return
        await event.message.edit_text(text=f"Terpilih rekening tujuan deposit: <b>{bank['bank_account_display']}</b>", reply_markup=None)
        user_model.action.set_action_data(ACTION_SUBMITTED_DEPOSIT_METHOD, "BANK")
        user_model.action.set_action_data(ACTION_SUBMITTED_DEPOSIT_CHANNEL_ID, channel_id)
        
        user_banks = user_model.action.get_action_data(ACTION_DATA_USER_BANKS)
        user_banks = sorted(user_banks, key=lambda r: r["bank_name"] != bank['bank_name'])
        user_model.action.set_action_data(ACTION_DATA_USER_BANKS, user_banks)
        await user_model.save_to_state()
        return await deposit_ask_user_bank(event, config, state, user_model, chat_id)
    elif method == "QRIS":
        payment_gateway = next((payment_gateway for payment_gateway in user_model.action.get_action_data(ACTION_DATA_QRIS_PAYMENT_GATEWAY) if payment_gateway["id"] == channel_id), None)
        if payment_gateway is None:
            await event.answer("Payment gateway tidak valid")
            return
        await event.message.edit_text(text=f"Terpilih payment gateway: <b>{payment_gateway['type']} - {payment_gateway['name']}</b>", reply_markup=None)
        user_model.action.set_action_data(ACTION_SUBMITTED_DEPOSIT_METHOD, "QRIS")
        user_model.action.set_action_data(ACTION_SUBMITTED_DEPOSIT_CHANNEL_ID, channel_id)
        await user_model.save_to_state()
        return await deposit_ask_amount(event, config, state, user_model, chat_id)
    elif method == "VA":
        virtual_account_payment_gateway = next((virtual_account_payment_gateway for virtual_account_payment_gateway in user_model.action.get_action_data(ACTION_DATA_VA_PAYMENT_GATEWAY) if virtual_account_payment_gateway["id"] == channel_id), None)
        if virtual_account_payment_gateway is None:
            await event.answer("Payment gateway tidak valid")
            return
        await event.message.edit_text(text=f"Terpilih payment gateway: <b>{virtual_account_payment_gateway['code']} {virtual_account_payment_gateway['type']} - {virtual_account_payment_gateway['name']}</b>", reply_markup=None)
        user_model.action.set_action_data(ACTION_SUBMITTED_DEPOSIT_METHOD, "VA")
        user_model.action.set_action_data(ACTION_SUBMITTED_DEPOSIT_CHANNEL_ID, channel_id)
        await user_model.save_to_state()
        return await deposit_ask_amount(event, config, state, user_model, chat_id)
    return

'''
Deposit Ask User Bank Function

Entrypoint:
- Deposit Channel Function (deposit_channel)
- Callback Button (data: deposit_ask_user_bank)
- Deposit Back Button Function (deposit_back_button_ask_user_bank)
'''
async def deposit_ask_user_bank(event: CallbackQuery, config: BotConfig, state: FSMContext, user_model: ModelUser, chat_id: int) -> None:
    if user_model.action is None or user_model.action.current_action != ACTION_DEPOSIT:
        await event.message.edit_text("Aksi tidak valid, silahkan ulangi proses deposit", reply_markup=None)
        await event.answer()
        return
    
    user_banks = user_model.action.get_action_data(ACTION_DATA_USER_BANKS)
    message = "Silahkan pilih rekening yang anda gunakan untuk melakukan deposit"
    builder = InlineKeyboardBuilder()
    for bank in user_banks:
        builder.add(InlineKeyboardButton(text=f"[{bank['bank_name']}] {bank['bank_account_number']} - {bank['bank_account_name']}", callback_data=f"deposit_choose_user_bank_{bank['id']}"))
    builder.adjust(1)
    navigation_builder = InlineKeyboardBuilder()
    navigation_builder.add(InlineKeyboardButton(text="🔙 Kembali", callback_data="deposit_back_button_ask_channel"))
    navigation_builder.add(InlineKeyboardButton(text="❌ Batalkan", callback_data="deposit_cancel"))
    navigation_builder.adjust(2)
    builder.attach(navigation_builder)
    if user_model.action.get_action_data(MESSAGE_MENU_DEPOSIT_USER_BANK) is not None:
        await bot.edit_message_text(chat_id=chat_id, message_id=user_model.action.get_action_data(MESSAGE_MENU_DEPOSIT_USER_BANK), text=message, reply_markup=builder.as_markup())
    else:
        message_id = (await event.message.answer(message, reply_markup=builder.as_markup())).message_id
        user_model.add_action_message_id(message_id)
        user_model.action.set_action_data(MESSAGE_MENU_DEPOSIT_USER_BANK, message_id)
    await user_model.save_to_state()
    await event.answer()
    return

'''
Deposit Choose User Bank Function

Entrypoint:
- Callback Button (data: deposit_choose_user_bank_{user_bank_id})
'''
async def deposit_choose_user_bank(event: CallbackQuery, config: BotConfig, state: FSMContext, user_model: ModelUser, chat_id: int) -> None:
    if user_model.action is None or user_model.action.current_action != ACTION_DEPOSIT:
        await event.message.edit_text("Aksi tidak valid, silahkan ulangi proses deposit", reply_markup=None)
        await event.answer()
        return
    
    try:
        user_bank_id = int(event.data.replace("deposit_choose_user_bank_", ""))
    except:
        await event.answer("Rekening tidak valid")
        return
    user_bank = next((bank for bank in user_model.action.get_action_data(ACTION_DATA_USER_BANKS) if bank["id"] == user_bank_id), None)
    if user_bank is None:
        await event.answer("Rekening tidak valid")
        return
    await event.message.edit_text(text=f"Terpilih rekening sebagai sumber dana: <b>[{user_bank['bank_name']}] {user_bank['bank_account_number']} - {user_bank['bank_account_name']}</b>", reply_markup=None)
    await state.set_state(LoggedInStates.deposit_ask_amount)
    user_model.action.set_action_data(ACTION_SUBMITTED_USER_BANK, user_bank_id)
    await user_model.save_to_state()
    if len(user_model.action.get_action_data(ACTION_DATA_PROMO)) > 0:
        return await deposit_ask_promo(event, config, state, user_model, chat_id)

    return await deposit_ask_amount(event, config, state, user_model, chat_id)

'''
Deposit Ask Promo Function

Entrypoint:
- Callback Button (data: deposit_choose_user_bank) (If any promo available)
'''
async def deposit_ask_promo(event: CallbackQuery, config: BotConfig, state: FSMContext, user_model: ModelUser, chat_id: int) -> None:
    if user_model.action is None or user_model.action.current_action != ACTION_DEPOSIT:
        await event.message.edit_text("Aksi tidak valid, silahkan ulangi proses deposit", reply_markup=None)
        await event.answer()
        return
    
    list_promo = user_model.action.get_action_data(ACTION_DATA_PROMO)
    message = """
Silahkan pilih promo yang tersedia

"""
    builder = InlineKeyboardBuilder()
    if list_promo is not None:
        for promo in list_promo:
            message += f"""<b>{promo['name']}</b>
Min. Deposit : <b>Rp.{promo['minimum_deposit']:,.0f}</b>
Turnover        : <b>{promo['turnover']}x</b>
Syarat WD     : <b>{promo['withdraw_requirement']}</b>
Frequency     : <b>{promo['frequency']}</b>
Amount          : <b>{promo['amount']}</b>

"""
            if promo['id'] == 0:
                builder.add(InlineKeyboardButton(text=f"{promo['name']}", callback_data=f"deposit_choose_promo_{promo['id']}"))
            else:
                builder.add(InlineKeyboardButton(text=f"{promo['name']}", callback_data=f"deposit_confirm_promo_{promo['id']}"))
    builder.adjust(1)

    navigation_builder = InlineKeyboardBuilder()
    navigation_builder.add(InlineKeyboardButton(text="🔙 Kembali", callback_data="deposit_back_button_ask_user_bank"))
    navigation_builder.add(InlineKeyboardButton(text="❌ Batalkan", callback_data="deposit_cancel"))
    navigation_builder.adjust(2)
    builder.attach(navigation_builder)
    if user_model.action.get_action_data(MESSAGE_MENU_DEPOSIT_PROMO) is not None:
        await bot.edit_message_text(chat_id=chat_id, message_id=user_model.action.get_action_data(MESSAGE_MENU_DEPOSIT_PROMO), text=message, reply_markup=builder.as_markup())
    else:
        message_id = (await event.message.answer(message, reply_markup=builder.as_markup())).message_id
        user_model.add_action_message_id(message_id)
        user_model.action.set_action_data(MESSAGE_MENU_DEPOSIT_PROMO, message_id)
    await user_model.save_to_state()
    await state.set_state(LoggedInStates.deposit_ask_note)
    return

'''
Deposit Confirm Promo Function

Entrypoint:
- Callback Button (data: deposit_confirm_promo_{promo_id})
'''
async def deposit_confirm_promo(event: CallbackQuery, config: BotConfig, state: FSMContext, user_model: ModelUser, chat_id: int) -> None:
    if user_model.action is None or user_model.action.current_action != ACTION_DEPOSIT:
        await event.message.edit_text("Aksi tidak valid, silahkan ulangi proses deposit", reply_markup=None)
        await event.answer()
        return
    promo_id: int = None
    try:
        promo_id = int(event.data.replace("deposit_confirm_promo_", ""))
    except:
        await event.answer("Promo tidak valid")
        return
    promo = next((promo for promo in user_model.action.get_action_data(ACTION_DATA_PROMO) if promo["id"] == promo_id), None)
    if promo is None:
        await event.answer("Promo tidak ditemukan")
        return

    message = f"""<b>Detail promo:</b>
Promo            : <b>{promo['name']}</b>
Min. Deposit : <b>Rp.{promo['minimum_deposit']:,.0f}</b>
Turnover        : <b>{promo['turnover']}x</b>
Syarat WD     : <b>{promo['withdraw_requirement']}</b>
Frequency     : <b>{promo['frequency']}</b>
Amount          : <b>{promo['amount']}</b>
"""
    if promo_id != 0:
        message += "Permainan untuk menyelesaikan promo:\n"
        for game_type, game in promo['products'].items():
            message += f"- <b>{game_type}</b>: {game}\n"
    else: 
        message += "Pilih Promo ini untuk melanjutkan proses deposit tanpa Promo"

    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🔙 Kembali", callback_data="deposit_back_button_ask_promo"))
    builder.add(InlineKeyboardButton(text="✅ Pilih Promo", callback_data=f"deposit_choose_promo_{promo_id}"))
    builder.adjust(2)
    if user_model.action.get_action_data(MESSAGE_MENU_DEPOSIT_PROMO) is not None:
        await bot.edit_message_text(chat_id=chat_id, message_id=user_model.action.get_action_data(MESSAGE_MENU_DEPOSIT_PROMO), text=message, reply_markup=builder.as_markup())
    else:
        message_id = (await event.message.answer(message, reply_markup=builder.as_markup())).message_id
        user_model.add_action_message_id(message_id)
        user_model.action.set_action_data(MESSAGE_MENU_DEPOSIT_PROMO, message_id)
    await user_model.save_to_state()
    await event.answer()
    return


'''
Deposit Choose Promo Function

Entrypoint:
- Callback Button (data: deposit_choose_promo_{promo_id})
'''
async def deposit_choose_promo(event: CallbackQuery, config: BotConfig, state: FSMContext, user_model: ModelUser, chat_id: int) -> None:
    if user_model.action is None or user_model.action.current_action != ACTION_DEPOSIT:
        await event.message.edit_text("Aksi tidak valid, silahkan ulangi proses deposit", reply_markup=None)
        await event.answer()
        return
    try:
        promo_id = int(event.data.replace("deposit_choose_promo_", ""))
    except:
        await event.answer("Promo tidak valid")
        return
    promo = next((promo for promo in user_model.action.get_action_data(ACTION_DATA_PROMO) if promo["id"] == promo_id), None)
    if promo is None:
        await event.answer("Promo tidak valid")
        return
    await event.message.edit_text(text=f"{event.message.text}\n<b>Promo Dipilih</b> ✅", reply_markup=None)
    await state.set_state(LoggedInStates.deposit_ask_note)
    user_model.action.set_action_data(ACTION_SUBMITTED_PROMO, promo_id)
    user_model.action.set_action_data(ACTION_DATA_MINIMUM_DEPOSIT, promo['minimum_deposit'])
    await user_model.save_to_state()
    return await deposit_ask_amount(event, config, state, user_model, chat_id)

'''
Deposit Ask Amount Function

Entrypoint:
- Deposit Select User Bank Function (deposit_choose_user_bank) (BANK)
- Deposit Channel Function (deposit_channel) (QRIS & VA)
'''
async def deposit_ask_amount(event: CallbackQuery, config: BotConfig, state: FSMContext, user_model: ModelUser, chat_id: int) -> None:
    if user_model.action is None or user_model.action.current_action != ACTION_DEPOSIT:
        await event.message.edit_text("Aksi tidak valid, silahkan ulangi proses deposit", reply_markup=None)
        await event.answer()
        return
    
    telegram_data = await model_utils.load_model(ModelTelegramData, state)
    cached_deposit_amounts = telegram_data.get_persistent_data(KEY_CACHED_DEPOSIT_AMOUNTS)
    if cached_deposit_amounts is None:
        cached_deposit_amounts = []
    
    maximum_deposit = int(user_model.action.get_action_data(ACTION_DATA_MAXIMUM_DEPOSIT))
    minimum_deposit = int(user_model.action.get_action_data(ACTION_DATA_MINIMUM_DEPOSIT))
    maximum_deposit = int(user_model.action.get_action_data(ACTION_DATA_MAXIMUM_DEPOSIT))
    
    message = f"Silahkan masukkan jumlah Deposit\nMinimal Deposit: <b>Rp.{minimum_deposit:,.0f}</b>\nMaksimal Deposit: <b>Rp.{maximum_deposit:,.0f}</b>"
    await state.set_state(LoggedInStates.deposit_ask_amount)
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="❌ Batalkan", callback_data="deposit_cancel"))
    for amount in cached_deposit_amounts:
        if amount >= minimum_deposit and amount <= maximum_deposit:
            builder.add(InlineKeyboardButton(text=f"Rp.{amount:,.0f}", callback_data=f"deposit_submit_amount_{amount}"))
    builder.adjust(4)
    message_id = (await event.message.answer(message, reply_markup=builder.as_markup())).message_id
    user_model.add_action_message_id(message_id)
    user_model.action.set_action_data(MESSAGE_MENU_DEPOSIT_AMOUNT, message_id)
    await user_model.save_to_state()
    await event.answer()
    return

'''
Deposit Submit Amount Function

Entrypoint:
- Callback Button (data: deposit_submit_amount_{amount})
- Message Router (text: {amount})
'''
async def deposit_submit_amount(event: CallbackQuery | Message, config: BotConfig, state: FSMContext, user_model: ModelUser, chat_id: int, telegram_data: ModelTelegramData) -> None:
    if user_model.action is None or user_model.action.current_action != ACTION_DEPOSIT:
        await event.message.edit_text("Aksi tidak valid, silahkan ulangi proses deposit", reply_markup=None)
        await event.answer()
        return
    
    amount: int | None = None
    try:
        if isinstance(event, CallbackQuery):
            user_model.add_action_message_id(event.message.message_id)
            amount = int(event.data.replace("deposit_submit_amount_", ""))
        else:
            user_model.add_action_message_id(event.message_id)
            amount = int(event.text)
    except ValueError:
        user_model.add_action_message_id((await event.answer("Jumlah deposit harus berupa angka, contoh: 10000")).message_id)
        return

    minimum_deposit = int(user_model.action.get_action_data(ACTION_DATA_MINIMUM_DEPOSIT))
    maximum_deposit = int(user_model.action.get_action_data(ACTION_DATA_MAXIMUM_DEPOSIT))
    deposit_method  = user_model.action.get_action_data(ACTION_SUBMITTED_DEPOSIT_METHOD)

    if deposit_method == "VA":
        minimum_deposit = 500000 #Hardcoded minimum deposit for VA
        maximum_deposit = 30000000 # Hardcoded maximum deposit for VA (30jt)

    if deposit_method == "QRIS":
        maximum_deposit = 10000000 # Hardcoded maximum deposit for QRIS (10jt)
    
    if amount is None or amount < minimum_deposit or amount > maximum_deposit:
        error_message = f"Jumlah deposit tidak valid, minimal Rp.{minimum_deposit:,.0f} dan maksimal Rp.{maximum_deposit:,.0f}"
        if isinstance(event, CallbackQuery):
            user_model.add_action_message_id((await event.message.answer(error_message, reply_markup=None)).message_id)
            return
        else:
            user_model.add_action_message_id((await event.answer(error_message)).message_id)
            return
    
    user_model.action.set_action_data(ACTION_SUBMITTED_DEPOSIT_AMOUNT, amount)
    await bot.edit_message_reply_markup(chat_id=chat_id, message_id=user_model.action.get_action_data(MESSAGE_MENU_DEPOSIT_AMOUNT), reply_markup=None)
    cached_deposit_amounts = telegram_data.get_persistent_data(KEY_CACHED_DEPOSIT_AMOUNTS)
    if cached_deposit_amounts is None:
        cached_deposit_amounts = []
    if amount not in cached_deposit_amounts:
        cached_deposit_amounts.insert(0, amount)
    if len(cached_deposit_amounts) >= 3:
        cached_deposit_amounts = cached_deposit_amounts[:3]
    telegram_data.set_persistent_data(KEY_CACHED_DEPOSIT_AMOUNTS, cached_deposit_amounts)
    await user_model.save_to_state()
    await telegram_data.save_to_state()

    if deposit_method == "BANK":
        await state.set_state(LoggedInStates.deposit_ask_note)
        return await deposit_ask_note(event, config, state, user_model, chat_id)
    await state.set_state(LoggedInStates.deposit_confirm)
    return await deposit_confirm(event, config, state, user_model, chat_id)

'''
Deposit Ask Note Function

Entrypoint:
- Deposit Ask Amount Function (deposit_ask_amount)
'''
async def deposit_ask_note(event: CallbackQuery | Message, config: BotConfig, state: FSMContext, user_model: ModelUser, chat_id: int) -> None:
    if user_model.action is None or user_model.action.current_action != ACTION_DEPOSIT:
        await event.message.edit_text("Aksi tidak valid, silahkan ulangi proses deposit", reply_markup=None)
        await event.answer()
        return

    message = "Silahkan masukkan catatan (Jika ada)"
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="❌ Batalkan", callback_data="deposit_cancel"))
    builder.add(InlineKeyboardButton(text="⏩ Lewati", callback_data="deposit_submit_note"))
    builder.adjust(2)
    message_id: int = None
    if isinstance(event, CallbackQuery):
        message_id = (await event.message.answer(message, reply_markup=builder.as_markup())).message_id
        await event.answer()
    elif isinstance(event, Message):
        message_id = (await event.answer(message, reply_markup=builder.as_markup())).message_id
    user_model.add_action_message_id(message_id)
    user_model.action.set_action_data(MESSAGE_MENU_DEPOSIT_NOTE, message_id)
    await user_model.save_to_state()
    await state.set_state(LoggedInStates.deposit_ask_note)
    return

'''
Deposit Submit Note Function

Entrypoint:
- Callback Button (data: deposit_submit_note)
- Message Router (state: LoggedInStates.deposit_ask_note)
'''
async def deposit_submit_note(event: CallbackQuery|Message, config: BotConfig, state: FSMContext, user_model: ModelUser, chat_id: int) -> None:
    if user_model.action is None or user_model.action.current_action != ACTION_DEPOSIT:
        if isinstance(event, CallbackQuery):
            await event.message.edit_text("Aksi tidak valid, silahkan ulangi proses deposit", reply_markup=None)
            await event.answer()
        else:
            await event.answer("Aksi tidak valid, silahkan ulangi proses deposit")
        await event.answer()
        return
    
    note = ""
    if isinstance(event, Message):
        note = sanitize_note(event.text)
        user_model.add_action_message_id(event.message_id)
        await bot.edit_message_reply_markup(chat_id=chat_id, message_id=user_model.action.get_action_data(MESSAGE_MENU_DEPOSIT_NOTE), reply_markup=None)
    elif isinstance(event, CallbackQuery):
        user_model.add_action_message_id(event.message.message_id)
        await event.message.edit_text(text="Tidak ada catatan yang dimasukkan", reply_markup=None)
        await event.answer()
    user_model.action.set_action_data(ACTION_SUBMITTED_NOTE, note)
    await user_model.save_to_state()
    return await deposit_confirm(event, config, state, user_model, chat_id)

'''
Ask Deposit Confirmation Function

Entrypoint:
- Deposit Ask Note Function (deposit_ask_note)
'''
async def deposit_confirm(event: CallbackQuery | Message, config: BotConfig, state: FSMContext, user_model: ModelUser, chat_id: int) -> None:
    # if user_model.action is None or user_model.action.current_action != ACTION_DEPOSIT:
    #     await event.message.edit_text("Aksi tidak valid, silahkan ulangi proses deposit", reply_markup=None)
    #     await event.answer()
    #     return
    
    amount = int(user_model.action.get_action_data(ACTION_SUBMITTED_DEPOSIT_AMOUNT))
    deposit_method = user_model.action.get_action_data(ACTION_SUBMITTED_DEPOSIT_METHOD)
    deposit_channel_id = user_model.action.get_action_data(ACTION_SUBMITTED_DEPOSIT_CHANNEL_ID)
    promo_id = user_model.action.get_action_data(ACTION_SUBMITTED_PROMO)
    channel_name: str | None = None
    bank_message_placeholder: str | None = ""
    if deposit_method == "BANK":
        channel_name = next((bank['bank_account_display'] for bank in user_model.action.get_action_data(ACTION_DATA_DEPOSIT_BANKS) if bank['id'] == deposit_channel_id), None)
    elif deposit_method == "QRIS":
        channel_name = next((payment_gateway['name'] for payment_gateway in user_model.action.get_action_data(ACTION_DATA_QRIS_PAYMENT_GATEWAY) if payment_gateway['id'] == deposit_channel_id), None)
    elif deposit_method == "VA":
        channel_name = next((f"{payment_gateway['description']} {payment_gateway['name']}" for payment_gateway in user_model.action.get_action_data(ACTION_DATA_VA_PAYMENT_GATEWAY) if payment_gateway['id'] == deposit_channel_id), None)
    
    if channel_name is None:
        await event.answer("Channel pembayaran tidak valid")
        return

    if deposit_method == "VA": # Show VA as Virtual Account
        deposit_method = "Virtual Account"
    
    
    if deposit_method == "BANK":
        user_bank = next((bank for bank in user_model.action.get_action_data(ACTION_DATA_USER_BANKS) if bank["id"] == user_model.action.get_action_data(ACTION_SUBMITTED_USER_BANK)), None)
        if user_bank is None:
            return
        bank_message_placeholder = f"Sumber Rekening Pembayaran: <b>[{user_bank['bank_name']}] {user_bank['bank_account_number']} - {user_bank['bank_account_name']}</b>\n"
        available_promo = user_model.action.get_action_data(ACTION_DATA_PROMO)
        if(available_promo is not None and len(available_promo) > 0):
            selected_promo = next((promo for promo in available_promo if promo["id"] == promo_id), None)
            if selected_promo is not None and promo_id is not None and promo_id != 0:
                bank_message_placeholder += f"Promo: <b>{selected_promo['name']}</b>\n"
                bank_message_placeholder += f"- Min. Deposit: <b>Rp.{selected_promo['minimum_deposit']:,.0f}</b>\n"
                bank_message_placeholder += f"- Turnover: <b>{selected_promo['turnover']}x</b>\n"
                bank_message_placeholder += f"- Syarat WD: <b>{selected_promo['withdraw_requirement']}</b>\n"
                bank_message_placeholder += f"- Frequency: <b>{selected_promo['frequency']}</b>\n"
                bank_message_placeholder += f"- Amount: <b>{selected_promo['amount']}</b>\n"
            elif promo_id == 0:
                bank_message_placeholder += "Promo: <b>Tidak ada promo yang dipilih</b>\n"
            

        notes = user_model.action.get_action_data(ACTION_SUBMITTED_NOTE)
        if notes is not None:
            notes = f"Catatan: <b>{notes}</b>\n"
        else:
            notes = ""
        bank_message_placeholder += notes

    message = f"""<b>Konfirmasi Deposit:</b>

Jumlah Deposit: <b>Rp.{amount:,.0f}</b>
Metode Pembayaran: <b>{deposit_method}</b>
Channel Pembayaran: <b>{channel_name}</b>
{bank_message_placeholder}
Apakah Anda yakin ingin melanjutkan proses deposit? Silahkan klik tombol "Konfirmasi" untuk melanjutkan proses deposit.

"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="❌ Batalkan", callback_data="deposit_cancel"))
    builder.add(InlineKeyboardButton(text="✅ Konfirmasi", callback_data=f"deposit_confirm_submit"))
    builder.adjust(2)
    if isinstance(event, CallbackQuery):
        user_model.add_action_message_id((await event.message.answer(message, reply_markup=builder.as_markup())).message_id)
        await event.answer()
        return
    else:
        user_model.add_action_message_id((await bot.send_message(chat_id, message, reply_markup=builder.as_markup())).message_id)
    return

'''
Deposit Submit Confirmation Function

Entrypoint:
- Callback Button (data: deposit_confirm_submit)
- Callback Button (data: deposit_confirm_submit_retry)
'''
async def deposit_confirm_submit(event: CallbackQuery, config: BotConfig, state: FSMContext, user_model: ModelUser, chat_id: int, api_client: OTPAPIClient) -> None:
    if user_model.action is None or user_model.action.current_action != ACTION_DEPOSIT:
        await event.message.edit_text("Aksi tidak valid, silahkan ulangi proses deposit", reply_markup=None)
        await event.answer()
        return
    
    if event.data == "deposit_confirm_submit_retry":
        await event.message.edit_text("Deposit diproses kembali...", reply_markup=None)

    deposit_method = user_model.action.get_action_data(ACTION_SUBMITTED_DEPOSIT_METHOD)
    channel_id = user_model.action.get_action_data(ACTION_SUBMITTED_DEPOSIT_CHANNEL_ID)
    user_bank_id = user_model.action.get_action_data(ACTION_SUBMITTED_USER_BANK)
    amount = user_model.action.get_action_data(ACTION_SUBMITTED_DEPOSIT_AMOUNT)
    notes = user_model.action.get_action_data(ACTION_SUBMITTED_NOTE)
    promo_id = user_model.action.get_action_data(ACTION_SUBMITTED_PROMO)
    promo = None

    message = f"""<b>Deposit berhasil dikonfirmasi</b>

<b>Jumlah Deposit:</b> <code>Rp.{amount:,.0f}</code>
<b>Metode Pembayaran:</b> <code>{deposit_method}</code>
"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="❌ Batalkan Deposit", callback_data="deposit_cancel"))
    builder.add(InlineKeyboardButton(text="✅ Coba Lagi", callback_data=f"deposit_confirm_submit_retry"))
    builder.adjust(2)
    if deposit_method == "BANK":
        response = await api_client.confirm_deposit_bank(user_bank_id=user_bank_id, deposit_bank_id=channel_id, promo_id=promo_id, amount=amount, notes=notes)
        if response.is_error:
            user_model.add_action_message_id((await event.message.answer(f"Gagal mengkonfirmasi deposit: {response.get_error_message()}", reply_markup=builder.as_markup())).message_id)
            if response.has_validation_errors:
                for field, errors in response.metadata.get('validation', {}).items():
                    for error in errors:
                        user_model.add_action_message_id((await event.message.answer(f"Validasi Error: {error}")).message_id)
            return
            
        deposit_bank = next((bank for bank in user_model.action.get_action_data(ACTION_DATA_DEPOSIT_BANKS) if bank["id"] == int(channel_id)), None)
        user_bank = next((bank for bank in user_model.action.get_action_data(ACTION_DATA_USER_BANKS) if bank["id"] == int(user_bank_id)), None)
        message += f"<b>Rekening Tujuan:</b> <code>{deposit_bank['bank_account_display']}</code>\n"
        message += f"<b>Rekening Sumber:</b> <code>{user_bank['bank_name']} {user_bank['bank_account_number']} - {user_bank['bank_account_name']}</code>\n"
        
        if promo_id is not None and promo_id != 0:
            promo = next((promo for promo in user_model.action.get_action_data(ACTION_DATA_PROMO) if promo["id"] == promo_id), None)
            if promo is not None:
                message += f"<b>Promo:</b> <code>{promo['name']}</code>\n"
                message += f"- <b>Turnover:</b> <code>{promo['turnover']}x</code>\n"
                message += f"- <b>Syarat WD:</b> <code>{promo['withdraw_requirement']}</code>\n"
                message += f"- <b>Frequency:</b> <code>{promo['frequency']}</code>\n"
                message += f"- <b>Amount:</b> <code>{promo['amount']}</code>\n"

    elif deposit_method == "QRIS" or deposit_method == "VA":
        payment_gateway = None
        if deposit_method == "QRIS": payment_gateway = next((payment_gateway for payment_gateway in user_model.action.get_action_data(ACTION_DATA_QRIS_PAYMENT_GATEWAY) if payment_gateway["id"] == channel_id), None)
        elif deposit_method == "VA": payment_gateway = next((payment_gateway for payment_gateway in user_model.action.get_action_data(ACTION_DATA_VA_PAYMENT_GATEWAY) if payment_gateway["id"] == channel_id), None)
        
        if payment_gateway is None:
            await event.message.answer(f"Payment gateway tidak ditemukan", reply_markup=builder.as_markup())
            return
        message += f"<b>Payment Gateway:</b> <code>{payment_gateway['name']}</code>\n"
        response = await api_client.confirm_deposit_payment_gateway(payment_gateway_id=payment_gateway['name'], amount=amount, type=deposit_method)
        if response.is_error:
            user_model.add_action_message_id((await event.message.answer(f"Gagal mengkonfirmasi deposit: {response.get_error_message()}", reply_markup=builder.as_markup())).message_id)
            if response.has_validation_errors:
                for field, errors in response.metadata.get('validation', {}).items():
                    for error in errors:
                        user_model.add_action_message_id((await event.message.answer(f"Validasi Error: {error}")).message_id)
            return
        
        if deposit_method == "QRIS":
            message += f"<b>Valid hingga:</b> <code>{response.data.get('expiredDate')} WIB</code>\n"
            message += f"<b>Reference ID:</b> <code>{response.data.get('merchant_ref').split('_')[1]}</code>\n"
            message += f"Silahkan melakukan pembayaran dengan scan QRIS berikut:"
        elif deposit_method == "VA":
            message += f"Silahkan melakukan transfer ke Virtual Account berikut: <code>{response.data.get('payment')}</code>"
    await event.message.answer(message)
    if deposit_method == "QRIS": await event.message.answer_photo(photo=response.data.get('payment'))
    await user_model.await_finish_action()
    await user_model.save_to_state()
    await state.set_state(LoggedInStates.main_menu)
    return 

async def deposit_cancel(event: CallbackQuery, config: BotConfig, state: FSMContext, user_model: ModelUser, chat_id: int) -> None:
    if user_model.action is None or user_model.action.current_action != ACTION_DEPOSIT:
        await event.message.delete()
        await event.answer()
        return
    
    user_model.finish_action()
    await event.answer("Proses deposit dibatalkan")
    return

'''
Deposit Back Button Function

Entrypoint:
- Callback Button (data: deposit_back_button_{navigation_to})
'''
async def deposit_back_button(event: CallbackQuery, config: BotConfig, state: FSMContext, user_model: ModelUser, chat_id: int) -> None:
    if user_model.action is None or user_model.action.current_action != ACTION_DEPOSIT:
        await event.message.edit_text("Aksi tidak valid, silahkan ulangi proses deposit", reply_markup=None)
        await event.answer()
        return
    
    navigation_to = event.data.replace("deposit_back_button_", "")

    print("Navigation To: ", navigation_to)
    if navigation_to == "ask_method":
        await event.message.delete()
        user_model.action.set_action_data(MESSAGE_MENU_DEPOSIT_CHANNEL, None)
        return await deposit_ask_method(event, config, state, user_model, chat_id)
    elif navigation_to == "ask_channel":
        await event.message.delete()
        user_model.action.set_action_data(MESSAGE_MENU_DEPOSIT_USER_BANK, None)
        return await deposit_ask_channel(event, config, state, user_model, chat_id)
    elif navigation_to == "ask_user_bank":
        await event.message.delete()
        user_model.action.set_action_data(MESSAGE_MENU_DEPOSIT_PROMO, None)
        return await deposit_ask_user_bank(event, config, state, user_model, chat_id)
    elif navigation_to == "ask_promo":
        return await deposit_ask_promo(event, config, state, user_model, chat_id)
    elif navigation_to == "ask_note":
        return await deposit_ask_note(event, config, state, user_model, chat_id)
    elif navigation_to == "ask_amount":
        return await deposit_ask_amount(event, config, state, user_model, chat_id)
    return

def sanitize_note(text: str) -> str:
    if text is None:
        return ""
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\n", " ").replace("\r", " ").replace("\t", " ")
    text = re.sub(r"\s{2,}", " ", text)
    text = "".join(ch for ch in text if ch.isprintable())
    return text.strip()