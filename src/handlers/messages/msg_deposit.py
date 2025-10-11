from aiogram import Router, types
from aiogram.types.contact import Contact
from aiogram.fsm.context import FSMContext
from aiogram.types.inline_keyboard_button import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import BotConfig
from models.model_user import ModelUser
import utils.validators as validators
from bot_instance import LoggedInStates
from keyboards.inline import keyboard_guest

async def msg_deposit_ask_amount(msg: types.Message, config: BotConfig, state: FSMContext, user_model: ModelUser) -> None:
    if msg.text is None:
        user_model.add_message_id((await msg.answer("Silahkan ketikkan jumlah deposit, contoh: 10000")).message_id)
        return
    
    if not validators.numeric(msg.text):
        user_model.add_message_id((await msg.answer("Jumlah deposit harus berupa angka, contoh: 10000")).message_id)
        return
    
    if not validators.int_min(msg.text, user_model.min_deposit) or not validators.int_max(msg.text, user_model.max_deposit):
        user_model.add_message_id((await msg.answer(f"Jumlah deposit harus minimal {user_model.min_deposit} dan maksimal {user_model.max_deposit}")).message_id)
        return
    
    user_model.set_deposit_amount(msg.text)

    await state.set_state(LoggedInStates.deposit_ask_channel)
    builder = InlineKeyboardBuilder()
    # if user_model.get_deposit_channels_by_type("bank") is not None:
    builder.add(InlineKeyboardButton(text="Bank (Coming Soon)", callback_data="deposit_ask_channel_BANK"))
    if user_model.get_deposit_channels_by_type("QRIS") is not None:
        builder.add(InlineKeyboardButton(text="QRIS", callback_data="deposit_ask_channel_QRIS"))
    if user_model.get_deposit_channels_by_type("VA") is not None:
        builder.add(InlineKeyboardButton(text="Virtual Account", callback_data="deposit_ask_channel_VA"))
    builder.adjust(1)
    user_model.add_message_id((await msg.answer("Silahkan pilih channel pembayaran", reply_markup=builder.as_markup())).message_id)

    return
