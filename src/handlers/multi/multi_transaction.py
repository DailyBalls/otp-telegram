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
    response = await api_client.show_deposit_withdraw_history()
    if response.is_error:
        await event.answer(f"Gagal memuat riwayat transaksi: {response.get_error_message()}")
        return
    
    if response.data is None:
        await event.answer("Gagal menerima informasi riwayat transaksi")
        return
    
    if isinstance(event, CallbackQuery):
        await event.answer("Menampilkan riwayat transaksi...")
    
    message_text = f"""
<b>Riwayat Transaksi</b>
📥: Deposit | 📤: Withdraw
🕒: Diproses | ❌: Ditolak | ✅: Berhasil

"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="↩️ Tutup", callback_data="action_close_with_answer_"))
    builder.adjust(1)
    for transaction in response.data.get("transactions", []):
        transaction = ModelTransaction(**transaction)
        message_text += f"{transaction.get_transaction_type_icon()} | Rp.{transaction.amount:,.0f} | {transaction.lastUpdate} | {transaction.get_report_type_icon()}\n"
    user_model.add_message_id((await bot.send_message(chat_id, message_text, reply_markup=builder.as_markup())).message_id)
    await user_model.save_to_state()
    return