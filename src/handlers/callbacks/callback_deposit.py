from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.types.inline_keyboard_button import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot_instance import LoggedInStates
from config import BotConfig
from models.model_user import ModelUser

async def callback_deposit_init(callback: types.CallbackQuery, config: BotConfig, state: FSMContext, user_model: ModelUser) -> None:
    await callback.answer("Memulai proses deposit...")

    user_model.add_message_id((await callback.message.answer("Silahkan ketikkan jumlah deposit, contoh: 10000")).message_id)
    await state.set_state(LoggedInStates.deposit_ask_amount)
    
    return

async def callback_deposit_ask_channel(callback: types.CallbackQuery, config: BotConfig, state: FSMContext, user_model: ModelUser) -> None:
    await callback.answer("Memulai proses deposit...")

    deposit_channel_type = callback.data.replace("deposit_ask_channel_", "")
    if deposit_channel_type == "BANK":
        user_model.add_message_id((await callback.message.answer("Pembayaran via Bank masih dalam tahap pengembangan")).message_id)
        await state.set_state(LoggedInStates.main_menu)
    elif deposit_channel_type == "QRIS" or deposit_channel_type == "VA":
        builder = InlineKeyboardBuilder()
        for channel in user_model.get_deposit_channels_by_type(deposit_channel_type):
            builder.add(InlineKeyboardButton(text=channel.name, callback_data=f"deposit_ask_pg_channel_{deposit_channel_type}_{channel.code}"))
        builder.adjust(4)
        user_model.add_message_id((await callback.message.answer(f"[{'QRIS' if deposit_channel_type == 'QRIS' else 'Virtual Account'}] Silahkah pilih Payment Gateway", reply_markup=builder.as_markup())).message_id)
        await state.set_state(LoggedInStates.deposit_ask_channel_payment_gateway)
    
    return