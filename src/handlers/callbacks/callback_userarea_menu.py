from aiogram import types
from aiogram.fsm.context import FSMContext

from bot_instance import LoggedInStates
from config import BotConfig
from models.model_deposit import DepositChannel
from models.model_user import ModelUser
from services.otp_services.api_client import OTPAPIClient

async def callback_userarea_menu_deposit(callback: types.CallbackQuery, config: BotConfig, state: FSMContext, user_model: ModelUser, api_client: OTPAPIClient) -> None:
    await callback.answer("Memulai proses deposit...")
    
    deposit_payment_channel = await api_client.deposit_payment_channel()
    if deposit_payment_channel.is_error:
        await callback.answer(f"Gagal memuat channel pembayaran")
        return
    
    if deposit_payment_channel.data is None:
        await callback.answer(f"Gagal menerima informasi channel pembayaran")
        return
    
    # Parse deposit payment channels data
    channels = []
    for channel in deposit_payment_channel.data:
        channels.append(DepositChannel(**channel))
    
    user_model.set_deposit_channels(channels)

    user_model.add_message_id((await callback.message.answer("Silahkan ketikkan jumlah deposit, contoh: 10000")).message_id)
    await state.set_state(LoggedInStates.deposit_ask_amount)
    
    return