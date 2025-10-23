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

ACTION_DEPOSIT = "deposit"
KEY_CACHED_DEPOSIT_AMOUNTS = "cached_deposit_amounts"
ACTION_DATA_MINIMUM_DEPOSIT = "minimum_deposit"
ACTION_DATA_MAXIMUM_DEPOSIT = "maximum_deposit"
ACTION_DATA_DEPOSIT_AMOUNT = "deposit_amount"
ACTION_DATA_USER_BANKS = "user_banks"
ACTION_DATA_DEPOSIT_BANKS = "deposit_banks"
ACTION_DATA_QRIS_PAYMENT_GATEWAY = "qris_payment_gateway"
ACTION_DATA_VA_PAYMENT_GATEWAY = "va_payment_gateway"

BANK_STATUS_OFFLINE = 0
BANK_STATUS_ONLINE = 1
BANK_STATUS_MAINTENANCE = 2

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

class PaymentGateway(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    type: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None

async def deposit_init(event: Message | CallbackQuery, config: BotConfig, state: FSMContext, user_model: ModelUser, chat_id: int, api_client: OTPAPIClient, telegram_data: ModelTelegramData) -> None:
    if user_model.action is not None:
        await user_model.action.finish()
    
    response = await api_client.initiate_deposit()
    if response.is_error:
        await event.answer(f"Gagal memulai proses deposit: {response.get_error_message()}")
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

    payment_gateway = response.data.get("payment_gateway", None)

    qris_payment_gateway: List[PaymentGateway] = []
    for payment_gateway in payment_gateway.get("QRIS", []):
        qris_payment_gateway.append(PaymentGateway(**payment_gateway))

    va_payment_gateway: List[PaymentGateway] = []
    for payment_gateway in payment_gateway.get("VA", []):
        va_payment_gateway.append(PaymentGateway(**payment_gateway))

    user_model.initiate_action(ACTION_DEPOSIT)
    user_model.action.set_action_data(ACTION_DATA_MINIMUM_DEPOSIT, response.data.get("min_deposit", 10000))
    user_model.action.set_action_data(ACTION_DATA_MAXIMUM_DEPOSIT, response.data.get("max_deposit", 1000000))
    user_model.action.set_action_data(ACTION_DATA_USER_BANKS, user_banks)
    user_model.action.set_action_data(ACTION_DATA_DEPOSIT_BANKS, deposit_banks)
    user_model.action.set_action_data(ACTION_DATA_QRIS_PAYMENT_GATEWAY, qris_payment_gateway)
    user_model.action.set_action_data(ACTION_DATA_VA_PAYMENT_GATEWAY, va_payment_gateway)

    cached_deposit_amounts = telegram_data.get_persistent_data(KEY_CACHED_DEPOSIT_AMOUNTS)
    if cached_deposit_amounts is None:
        cached_deposit_amounts = []

    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="❌ Batalkan", callback_data="deposit_cancel"))
    has_cached_amount = False
    cached_deposit_amounts.sort()
    for amount in cached_deposit_amounts:
        builder.add(InlineKeyboardButton(text=f"Rp.{amount:,.0f}", callback_data=f"deposit_amount_{amount}"))
    builder.adjust(6)
    reply_text = "Silahkan ketik jumlah deposit, contoh: 10000" if not has_cached_amount else "Silahkan pilih jumlah deposit atau ketik jumlah deposit, contoh: 10000"
    reply_message = await bot.send_message(chat_id, reply_text, reply_markup=builder.as_markup())
    user_model.add_action_message_id(reply_message.message_id)
    await state.set_state(LoggedInStates.deposit_ask_amount)
    await user_model.save_to_state()
    return

async def deposit_input_amount(event: Message | CallbackQuery, config: BotConfig, state: FSMContext, user_model: ModelUser, chat_id: int, api_client: OTPAPIClient, telegram_data: ModelTelegramData) -> None:
    if user_model.action is None or user_model.action.current_action != ACTION_DEPOSIT:
        if isinstance(event, CallbackQuery):
            await event.message.edit_text("Aksi tidak valid, silahkan ulangi proses deposit", reply_markup=None)
            await event.answer()
            return
        else:
            await event.answer("Silahkan ulangi proses deposit dengan mengetik /deposit")
            return
    
    amount: int | None = None
    try:
        if isinstance(event, CallbackQuery):
            await event.answer()
            amount = int(event.data.replace("deposit_amount_", ""))
        else:
            amount = int(event.text)
            user_model.add_action_message_id(event.message_id)
    except ValueError:
        user_model.add_action_message_id((await event.answer("Jumlah deposit harus berupa angka, contoh: 10000")).message_id)
        return
    
    if amount is None or amount < user_model.action.get_action_data(ACTION_DATA_MINIMUM_DEPOSIT) or amount > user_model.action.get_action_data(ACTION_DATA_MAXIMUM_DEPOSIT):
        error_message = f"Jumlah deposit tidak valid, minimal Rp.{user_model.action.get_action_data(ACTION_DATA_MINIMUM_DEPOSIT):,.0f} dan maksimal Rp.{user_model.action.get_action_data(ACTION_DATA_MAXIMUM_DEPOSIT):,.0f}"
        if isinstance(event, CallbackQuery):
            user_model.add_action_message_id((await event.message.answer(error_message, reply_markup=None)).message_id)
            return
        else:
            user_model.add_action_message_id((await event.answer(error_message)).message_id)
            return
    
    await state.set_state(LoggedInStates.deposit_ask_method)
    user_model.action.set_action_data(ACTION_DATA_DEPOSIT_AMOUNT, amount)

    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Bank", callback_data=f"deposit_ask_channel_BANK"))
    if user_model.get_deposit_channels_by_type("QRIS") is not None:
        builder.add(InlineKeyboardButton(text="QRIS", callback_data=f"deposit_ask_channel_QRIS"))
    if user_model.get_deposit_channels_by_type("VA") is not None:
        builder.add(InlineKeyboardButton(text="Virtual Account", callback_data=f"deposit_ask_channel_VA"))
    builder.add(InlineKeyboardButton(text="❌ Batalkan", callback_data="deposit_cancel"))
    builder.adjust(2)
    reply_message = await bot.send_message(chat_id, "Silahkan pilih metode pembayaran", reply_markup=builder.as_markup())
    user_model.add_action_message_id(reply_message.message_id)
    await user_model.save_to_state()
    return
    
async def deposit_ask_channel(event: CallbackQuery, config: BotConfig, state: FSMContext, user_model: ModelUser, chat_id: int) -> None:
    if user_model.action is None or user_model.action.current_action != ACTION_DEPOSIT:
        await event.message.edit_text("Aksi tidak valid, silahkan ulangi proses deposit", reply_markup=None)
        await event.answer()
        return
        
    route = event.data.replace("deposit_ask_channel_", "").split("_")
    method = route[0]
    if method not in ["BANK", "QRIS", "VA"]:
        user_model.add_action_message_id((await bot.send_message(chat_id, "Metode pembayaran tidak valid", reply_markup=None)).message_id)
        await event.answer()
        return
    if method == "BANK":
        await event.message.edit_text("Pembayaran via Bank masih dalam tahap pengembangan", reply_markup=None)
        await event.answer()
        return
    
    if method == "QRIS":
        await event.message.edit_text("Pembayaran via QRIS masih dalam tahap pengembangan", reply_markup=None)
        await event.answer()
        return
    
    if method == "VA":
        await event.message.edit_text("Pembayaran via Virtual Account masih dalam tahap pengembangan", reply_markup=None)
        await event.answer()
        return
    
    