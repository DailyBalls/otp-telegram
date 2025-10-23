from datetime import datetime
from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.types.inline_keyboard_button import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot_instance import LoggedInStates, bot
from config import BotConfig
from handlers.callbacks.callback_action import callback_action_cancel
from models.model_action import ModelAction
from models.model_deposit import DepositChannel
from models.model_user import ModelUser
from services.otp_services.api_client import OTPAPIClient
from utils import validators
import utils.models as model_utils

ALLOWED_DEPOSIT_CHANNEL_TYPES = ["QRIS", "VA", "BANK"]
ACTION_DEPOSIT = "deposit"

async def callback_deposit_init(callback: types.CallbackQuery, config: BotConfig, state: FSMContext, user_model: ModelUser, api_client: OTPAPIClient) -> None:
    action_model: ModelAction | None = await model_utils.load_model(ModelAction, state)
    if action_model is not None:
        await action_model.delete_all_messages()
        # await action_model.delete_from_state()

    action_model = ModelAction(current_action=ACTION_DEPOSIT, state=state, chat_id=callback.message.chat.id)
    
    list_deposit_payment_channel = await api_client.list_deposit_payment_channel()
    if list_deposit_payment_channel.is_error:
        await callback.answer(f"Gagal memuat channel pembayaran")
        return
    
    if list_deposit_payment_channel.data is None:
        await callback.answer(f"Gagal menerima informasi channel pembayaran")
        return
    
    await callback.answer("Memulai proses deposit...")

    # Parse deposit payment channels data
    channels = []
    for channel in list_deposit_payment_channel.data:
        channels.append(DepositChannel(**channel))
    
    user_model.set_deposit_channels(channels)

    await state.set_state(LoggedInStates.deposit_ask_amount)
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Batalkan", callback_data="deposit_cancel"))
    builder.adjust(1)
    answer = await callback.message.answer("Masukkan jumlah deposit, contoh: 10000", reply_markup=builder.as_markup())
    action_model.add_message_id(answer.message_id)
    user_model.add_message_id(answer.message_id)
    await action_model.save_to_state()
    return


async def ask_payment_method(amount: str, state: FSMContext, user_model: ModelUser, action_model: ModelAction, callback: types.CallbackQuery = None) -> None:
    
    amount = amount.strip()
    if not validators.numeric(amount):
        user_model.add_message_id((await bot.send_message(chat_id=action_model.chat_id, text="Jumlah deposit harus berupa angka, contoh: 10000")).message_id)
        await user_model.save_to_state()
        return
    
    if not validators.int_min(amount, user_model.min_deposit) or not validators.int_max(amount, user_model.max_deposit):
        user_model.add_message_id((await bot.send_message(chat_id=action_model.chat_id, text=f"Jumlah deposit harus minimal {user_model.min_deposit} dan maksimal {user_model.max_deposit}")).message_id)
        await user_model.save_to_state()
        return

    await state.set_state(LoggedInStates.deposit_ask_method)
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Bank (Coming Soon)", callback_data=f"deposit_ask_channel_BANK_{amount}"))
    if user_model.get_deposit_channels_by_type("QRIS") is not None:
        builder.add(InlineKeyboardButton(text="QRIS", callback_data=f"deposit_ask_channel_QRIS_{amount}"))
    if user_model.get_deposit_channels_by_type("VA") is not None:
        builder.add(InlineKeyboardButton(text="Virtual Account", callback_data=f"deposit_ask_channel_VA_{amount}"))
    builder.adjust(1)
    if callback is None:
        answer = await bot.send_message(chat_id=action_model.chat_id, text="Silahkan pilih metode pembayaran", reply_markup=builder.as_markup())
        action_model.add_message_id(answer.message_id)
        user_model.add_message_id(answer.message_id)
        await action_model.save_to_state()
    else:
        await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id, text="Silahkan pilih metode pembayaran", reply_markup=builder.as_markup())
    return

async def callback_deposit_ask_payment_method(callback: types.CallbackQuery, config: BotConfig, state: FSMContext, user_model: ModelUser) -> None:
    action_model: ModelAction | None = await model_utils.load_model(ModelAction, state)
    if action_model is None:
        await callback.message.delete()
        await callback.answer("Silahkan ulangi proses deposit")
        return

    await callback.answer()
    data = callback.data.replace("deposit_ask_method_", "").split("_")
    deposit_method_amount = data[0]

    await ask_payment_method(deposit_method_amount, state, user_model, action_model, callback)

async def callback_deposit_ask_channel(callback: types.CallbackQuery, config: BotConfig, state: FSMContext, user_model: ModelUser) -> None:
    action_model: ModelAction | None = await model_utils.load_model(ModelAction, state)
    if action_model is None:
        await callback.message.delete()
        await callback.answer("Silahkan ulangi proses deposit")
        return
    
    await callback.answer()
    action_model.add_message_id(callback.message.message_id)
    user_model.add_message_id(callback.message.message_id)

    data = callback.data.replace("deposit_ask_channel_", "").split("_")
    deposit_channel_type = data[0]
    deposit_channel_amount = data[1]

    if not validators.int_between(deposit_channel_amount, user_model.min_deposit, user_model.max_deposit):
        action_model.add_message_id((await callback.answer(f"Jumlah deposit tidak valid")).message_id)
        return

    if deposit_channel_type not in ALLOWED_DEPOSIT_CHANNEL_TYPES:
        action_model.add_message_id((await callback.answer(f"Channel pembayaran tidak valid")).message_id)
        return

    # TODO: Handle bank deposit
    if deposit_channel_type == "BANK":
        await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id, text="Pembayaran via Bank masih dalam tahap pengembangan")
        await state.set_state(LoggedInStates.main_menu)

    # TODO: Handle QRIS deposit
    elif deposit_channel_type == "QRIS" or deposit_channel_type == "VA":
        builder = InlineKeyboardBuilder()
        for channel in user_model.get_deposit_channels_by_type(deposit_channel_type):
            builder.add(InlineKeyboardButton(text=f"{channel.name} - {channel.description}", callback_data=f"deposit_confirm_channel_{deposit_channel_amount}_{deposit_channel_type}_{channel.name}_{channel.code}"))
        builder.adjust(1)

        cancel_back_builder = InlineKeyboardBuilder()
        cancel_back_builder.add(InlineKeyboardButton(text="Kembali", callback_data=f"deposit_ask_method_{deposit_channel_amount}"))
        cancel_back_builder.add(InlineKeyboardButton(text="Batalkan", callback_data=f"action_cancel"))
        cancel_back_builder.adjust(2)
        builder.attach(cancel_back_builder)

        await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id, text="Silahkan pilih channel pembayaran", reply_markup=builder.as_markup())
        await state.set_state(LoggedInStates.deposit_ask_channel_payment_gateway)
    
    return

async def callback_deposit_confirm_channel(callback: types.CallbackQuery, config: BotConfig, state: FSMContext, user_model: ModelUser) -> None:
    action_model: ModelAction | None = await model_utils.load_model(ModelAction, state)
    if action_model is None:
        await callback.answer("Silahkan ulangi proses deposit")
        await callback.message.delete()
        return
    
    await callback.answer()
    data = callback.data.replace("deposit_confirm_channel_", "").split("_")
    deposit_channel_amount = data[0] # 10000, 20000, etc...
    deposit_channel_type   = data[1] # QRIS, VA, BANK
    deposit_channel_name   = data[2] # TOPAY, SIPAY, DAPAY, etc...
    deposit_channel_code   = data[3] # QR, BRI, BNI, etc..
    
    # user_model.set_deposit_channel(DepositChannel(name=deposit_channel_name, type=deposit_channel_type, code=deposit_channel_code))
    if deposit_channel_type == "QRIS":
        message = f"""
<b>Konfirmasi Pembayaran:</b>

Jumlah deposit: <b>{deposit_channel_amount}</b>
Metode pembayaran: <b>{deposit_channel_type} - {deposit_channel_code}</b>
Payment Gateway: <b>{deposit_channel_name}</b>

Apakah anda yakin ingin melanjutkan?
        """
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="Ya", callback_data=f"deposit_confirm_yes_{deposit_channel_amount}_{deposit_channel_type}_{deposit_channel_name}_{deposit_channel_code}"))
        builder.add(InlineKeyboardButton(text="Tidak", callback_data=f"deposit_confirm_no_{deposit_channel_amount}_{deposit_channel_type}_{deposit_channel_name}_{deposit_channel_code}"))
        builder.adjust(2)
        await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id, text=message, reply_markup=builder.as_markup())
        # user_model.add_message_id((await callback.message.answer(message, reply_markup=builder.as_markup())).message_id)
        await state.set_state(LoggedInStates.deposit_confirm_channel)
    return

async def callback_deposit_confirm_yes(callback: types.CallbackQuery, config: BotConfig, state: FSMContext, user_model: ModelUser) -> None:
    data = callback.data.replace("deposit_confirm_yes_", "").split("_")
    deposit_channel_amount = data[0] # 10000, 20000, etc...
    deposit_channel_type = data[1] # QRIS, VA, BANK
    deposit_channel_name = data[2] # TOPAY, SIPAY, DAPAY, etc..
    deposit_channel_code = data[3] # QR, BRI, BNI, etc..
    action_model: ModelAction | None = await model_utils.load_model(ModelAction, state)
    await callback.answer()
    if action_model is not None:
        print("Unsetting message id", callback.message.message_id)
        action_model.unset_message_id(callback.message.message_id)
        await action_model.save_to_state()
    user_model.unset_message_id(callback.message.message_id)
    if deposit_channel_type == "QRIS":
        await callback.message.delete()
        caption = f"""
<b>Segera lakukan pembayaran</b>
<b>Username:</b> <code>{user_model.username}</code>
<b>Jumlah deposit:</b> <code>{deposit_channel_amount}</code>
<b>Metode pembayaran:</b> <code>{deposit_channel_type} - {deposit_channel_code}</code>
<b>Payment Gateway:</b> <code>{deposit_channel_name}</code>
<b>Waktu Pembuatan:</b> <code>{datetime.now().strftime("%d %B %Y %H:%M:%S")} WIB</code>
<b>Waktu Expire:</b> <code>Selasa, 12 Oktober 2025 12:00 WIB</code>
<b>Reference ID:</b> <code>REF_XXXXXXXXXXXXXXXXX</code>
<b>Silahkan scan QRIS Berikut:</b>"""
        photo_url = "https://otp.nahbisa.com/images/payment-qr.png"
        await callback.message.answer(text=caption)
        await callback.message.answer_photo(photo=photo_url)
        # await bot.send_photo(chat_id=callback.message.chat.id, photo=photo_url, caption=caption)
    elif deposit_channel_type == "VA":
        await callback.message.answer("Silahkan transfer ke Virtual Account <b>{deposit_channel_code}</b>")
    elif deposit_channel_type == "BANK":
        await callback.message.answer("Silahkan transfer ke Bank <b>{deposit_channel_code}</b>")
    
    await action_model.finish_action()
    return

async def callback_deposit_cancel(callback: types.CallbackQuery, config: BotConfig, state: FSMContext, user_model: ModelUser) -> None:
    action_model: ModelAction | None = await model_utils.load_model(ModelAction, state)
    current_state = await state.get_state()
    if "deposit" in current_state:
        await state.set_state(LoggedInStates.main_menu)

    if action_model is not None and action_model.current_action == ACTION_DEPOSIT:
        await action_model.finish_action()

    await callback.answer("Proses deposit dibatalkan")
    return