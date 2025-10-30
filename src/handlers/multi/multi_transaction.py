from contextlib import suppress
from datetime import datetime
from aiogram.types import InlineKeyboardButton, Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot_instance import bot
from config import BotConfig
from models.model_transaction import ModelTransaction
from models.model_user import ModelUser
from services.otp_services.api_client import OTPAPIClient
from models.model_telegram_data import ModelTelegramData

async def transaction_history(event: Message | CallbackQuery, config: BotConfig, state: FSMContext, user_model: ModelUser, chat_id: int, api_client: OTPAPIClient, telegram_data: ModelTelegramData) -> None:
    
    is_edit_message = False
    response = await api_client.show_deposit_withdraw_history()
    if response.is_error:
        await event.answer(f"Gagal memuat riwayat transaksi: {response.get_error_message()}")
        return
    
    if response.data is None:
        await event.answer("Gagal menerima informasi riwayat transaksi")
        return
    
    if isinstance(event, CallbackQuery):
        if event.data == "transaction_history_refresh":
            is_edit_message = True
            await event.answer("Berhasil memuat ulang riwayat transaksi...")
        else:
            await event.answer("Menampilkan riwayat transaksi...")
    
    message_text = f"""
<b>Riwayat Transaksi</b>
📥: Deposit | 📤: Withdraw
🕒: Diproses | ❌: Ditolak | ✅: Berhasil

"""
    message_text += f"Credit saat ini: <b>Rp.{float(response.data.get('user', {}).get('credit', 0)):,.0f}</b>\n"
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="↩️ Tutup", callback_data="action_close_with_answer_"))
    builder.add(InlineKeyboardButton(text="🔄 Refresh", callback_data="transaction_history_refresh"))
    builder.adjust(2)
    for transaction in response.data.get("transactions", []):
        transaction = ModelTransaction(**transaction)
        message_text += f"{transaction.get_transaction_type_icon()} | Rp.{transaction.amount:,.0f} | {transaction.lastUpdate} | {transaction.get_report_type_icon()}\n"

    message_text += f"\nWaktu terakhir update: <b>{datetime.now().strftime('%d-%m-%Y %H:%M')} WIB</b>"
    if is_edit_message:
        with suppress(Exception):
            await bot.edit_message_text(chat_id=chat_id, message_id=event.message.message_id, text=message_text, reply_markup=builder.as_markup())
    else:
        user_model.add_message_id((await bot.send_message(chat_id, message_text, reply_markup=builder.as_markup())).message_id)
    await user_model.save_to_state()
    return