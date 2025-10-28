from aiogram.types import InlineKeyboardButton, Message
from aiogram.fsm.context import FSMContext
from aiogram.types.callback_query import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot_instance import LoggedInStates, bot
from config import BotConfig
from models.model_action import ModelAction
from models.model_telegram_data import ModelTelegramData
from models.model_user import ModelUser
from services.otp_services import api_client
from services.otp_services.api_client import OTPAPIClient
import utils.models as model_utils

ACTION_WITHDRAW                  = "withdraw"
ACTION_DATA_MINIMUM_WITHDRAW     = "minimum_withdraw"
ACTION_DATA_MAXIMUM_WITHDRAW     = "maximum_withdraw"
ACTION_DATA_WITHDRAW_MULTIPLES   = "withdraw_multiples"
ACTION_DATA_WITHDRAW_AMOUNT      = "withdraw_amount"
ACTION_DATA_WITHDRAW_DESTINATION = "withdraw_destination"
KEY_CACHED_WITHDRAW_AMOUNTS      = "cached_withdraw_amounts"

KETENTUAN_WITHDRAW = """
<b>Ketentuan Withdraw :</b>
Mohon perhatikan Nama & Rekening adalah milik Anda.

<b>Kami hanya melakukan transfer ke rekening yang terdaftar dalam Akun pemain Anda.</b>

Catatan :
- Harap melakukan konfirmasi Withdraw satu kali saja
- Tunggu hingga permohonan anda diproses oleh staf kami
- Saldo akan masuk segera masuk ke rekening Anda
- Untuk penggantian rekening harap menghubungi CS kami

Minimal Withdraw: <b>Rp.{MINIMAL_WITHDRAW:,.0f}</b>
Maksimal Withdraw: <b>Rp.{MAXIMAL_WITHDRAW:,.0f}</b>
Kelipatan Withdraw: <b>Rp.{WITHDRAW_MULTIPLES:,.0f}</b>
"""

def is_valid_withdraw_amount(amount: int, minimum_withdraw: int, maximum_withdraw: int, withdraw_multiples: int) -> bool:
    return amount <= maximum_withdraw and amount >= minimum_withdraw and amount % withdraw_multiples == 0

'''
Withdraw Init Function

Entrypoint:
- Callback Button (data: menu_withdraw)
- Message Router (text: Withdraw)
- Command Router (cmd: withdraw)
'''
async def withdraw_init(msg: Message | CallbackQuery, config: BotConfig, state: FSMContext, user_model: ModelUser, message_id: int, chat_id: int, api_client: OTPAPIClient, telegram_data: ModelTelegramData) -> None:
    if user_model.action is not None:
        await user_model.await_finish_action()
    
    user_model.initiate_action(ACTION_WITHDRAW)
    
    response = await api_client.initiate_withdraw(amount=0)
    if response.is_error:
        error_message = f"❌ Gagal memulai proses withdraw\nError: {response.get_error_message()}"
        if isinstance(msg, CallbackQuery):
            await msg.answer()
            await msg.message.answer(error_message)
        elif isinstance(msg, Message):
            await msg.answer(error_message)
        return

    if response.data.get("pending_wd", False) == True:

        await msg.answer("Masih ada Withdraw yang sedang berlangsung")
        return

    rekening_wd = response.data.get("rekening_wd", None)
    if rekening_wd is None:
        await msg.answer("Gagal memulai proses withdraw, Rekening Withdraw tidak ditemukan")
        return
    
    rekening_wd_name = rekening_wd.get("name", "")
    rekening_wd_account_number = rekening_wd.get("rekening", "")
    rekening_wd_bank = rekening_wd.get("bank", "")

    user_model.action.set_action_data(ACTION_DATA_MINIMUM_WITHDRAW, response.data.get("min_amount", 10000))
    user_model.action.set_action_data(ACTION_DATA_MAXIMUM_WITHDRAW, response.data.get("max_amount", 1000000))
    user_model.action.set_action_data(ACTION_DATA_WITHDRAW_MULTIPLES, response.data.get("withdraw_multiple", 1000))
    user_model.action.set_action_data(ACTION_DATA_WITHDRAW_DESTINATION, f"[{rekening_wd_bank}] {rekening_wd_account_number} - {rekening_wd_name}")
    
    ketentuan_withdraw = KETENTUAN_WITHDRAW.format(MINIMAL_WITHDRAW=user_model.action.get_action_data(ACTION_DATA_MINIMUM_WITHDRAW), MAXIMAL_WITHDRAW=user_model.action.get_action_data(ACTION_DATA_MAXIMUM_WITHDRAW), WITHDRAW_MULTIPLES=user_model.action.get_action_data(ACTION_DATA_WITHDRAW_MULTIPLES))
    if isinstance(msg, CallbackQuery):
        msg.answer()
        
    user_model.add_action_message_id((await bot.send_message(chat_id, ketentuan_withdraw)).message_id)
    await user_model.save_to_state()
    return await withdraw_ask_amount(msg, config, state, user_model, chat_id, telegram_data)

'''
Withdraw Ask Amount Function

Entrypoint:
- Init Function (withdraw_init)
'''
async def withdraw_ask_amount(event: CallbackQuery, config: BotConfig, state: FSMContext, user_model: ModelUser, chat_id: int, telegram_data: ModelTelegramData) -> None:
    if user_model.action is None or user_model.action.current_action != ACTION_WITHDRAW:
        await event.message.edit_text("Aksi tidak valid, silahkan ulangi proses withdraw", reply_markup=None)
        await event.answer()
        return
    
    cached_withdraw_amounts = telegram_data.get_persistent_data(KEY_CACHED_WITHDRAW_AMOUNTS)
    if cached_withdraw_amounts is None:
        cached_withdraw_amounts = []

    
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="❌ Batalkan", callback_data="withdraw_cancel"))
    
    '''
    has_cached_amount!? why not just check if len(cached_withdraw_amounts) > 0?
    since min_withdraw, max_withdraw, and withdraw_multiple are gathered from the API response,
    so it's possible that the cached_withdraw_amounts value is not a valid amount.
    '''
    has_cached_amount = False
    # cached_withdraw_amounts.sort()
    for amount in cached_withdraw_amounts:
        if is_valid_withdraw_amount(amount, user_model.action.get_action_data(ACTION_DATA_MINIMUM_WITHDRAW), user_model.action.get_action_data(ACTION_DATA_MAXIMUM_WITHDRAW), user_model.action.get_action_data(ACTION_DATA_WITHDRAW_MULTIPLES)):
            has_cached_amount = True
            builder.add(InlineKeyboardButton(text=f"Rp.{amount:,.0f}", callback_data=f"withdraw_amount_{amount}"))
    builder.adjust(6)
    reply_text = "Silahkan ketik jumlah withdraw, contoh: 10000" if not has_cached_amount else "Silahkan pilih jumlah withdraw atau ketik jumlah withdraw, contoh: 10000"
    reply_message = await bot.send_message(chat_id, reply_text, reply_markup=builder.as_markup())
    user_model.add_action_message_id(reply_message.message_id)
    await state.set_state(LoggedInStates.withdraw_ask_amount)
    await user_model.save_to_state()
    return

'''
Withdraw Input Amount Function

Entrypoint:
- Callback Button (data: withdraw_amount_{amount})
- Message Router (text: amount)
'''
async def withdraw_input_amount(callback: CallbackQuery | Message, config: BotConfig, state: FSMContext, user_model: ModelUser, message_id: int, chat_id: int) -> None:
    if user_model.action is None or user_model.action.current_action != ACTION_WITHDRAW:
        if isinstance(callback, CallbackQuery):
            await callback.message.edit_text("Aksi tidak valid, silahkan ulangi proses withdraw", reply_markup=None)
            await callback.answer()
            return
        else:
            await callback.answer("Silahkan ulangi proses withdraw dengan mengetik /withdraw")
            return
    
    amount: int | None = None
    try:
        if isinstance(callback, CallbackQuery):
            amount = int(callback.data.replace("withdraw_amount_", ""))
        else:
            amount = int(callback.text)
    except ValueError:
        user_model.add_action_message_id((await callback.answer("Jumlah withdraw harus berupa angka, contoh: 10000")).message_id)
        return
    
    if amount is None or amount < user_model.action.get_action_data(ACTION_DATA_MINIMUM_WITHDRAW) or amount > user_model.action.get_action_data(ACTION_DATA_MAXIMUM_WITHDRAW):
        error_message = f"Jumlah withdraw tidak valid, minimal Rp.{user_model.action.get_action_data(ACTION_DATA_MINIMUM_WITHDRAW):,.0f} dan maksimal Rp.{user_model.action.get_action_data(ACTION_DATA_MAXIMUM_WITHDRAW):,.0f}"
        if isinstance(callback, CallbackQuery):
            user_model.add_action_message_id((await callback.message.answer(error_message, reply_markup=None)).message_id)
            await user_model.save_to_state()
            await callback.answer()
            return
        else:
            user_model.add_action_message_id((await callback.answer(error_message)).message_id)
            await user_model.save_to_state()
            return

    if amount % user_model.action.get_action_data(ACTION_DATA_WITHDRAW_MULTIPLES) != 0:
        error_message = f"Jumlah withdraw harus kelipatan Rp.{user_model.action.get_action_data(ACTION_DATA_WITHDRAW_MULTIPLES):,.0f}"
        if isinstance(callback, CallbackQuery):
            user_model.add_action_message_id((await callback.message.answer(error_message, reply_markup=None)).message_id)
            await user_model.save_to_state()
            await callback.answer()
            return
        else:
            user_model.add_action_message_id((await callback.answer(error_message)).message_id)
            await user_model.save_to_state()
            return
    
    user_model.action.set_action_data(ACTION_DATA_WITHDRAW_AMOUNT, amount)
    user_model.add_action_message_id(message_id)
    message = f"""
<b>Konfirmasi Withdraw:</b>

Jumlah withdraw: <b>Rp.{user_model.action.get_action_data(ACTION_DATA_WITHDRAW_AMOUNT):,.0f}</b>
Rekening Withdraw: <b>{user_model.action.get_action_data(ACTION_DATA_WITHDRAW_DESTINATION)}</b>

Apakah Anda yakin ingin melanjutkan proses withdraw? Silahkan klik tombol <b>\"Konfirmasi\"</b> untuk melanjutkan proses withdraw.

NB: Jika anda ingin mengubah rekening withdraw, silahkan chat customer service kami
"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="❌ Batalkan", callback_data="withdraw_cancel"))
    builder.add(InlineKeyboardButton(text="✅ Konfimasi", callback_data="withdraw_confirm_yes"))
    builder.adjust(2)
    if isinstance(callback, CallbackQuery):
        reply_message = await callback.message.edit_text(message, reply_markup=builder.as_markup())
    else:
        reply_message = await bot.send_message(chat_id, message, reply_markup=builder.as_markup())
    user_model.add_action_message_id(reply_message.message_id)
    await state.set_state(LoggedInStates.withdraw_ask_confirm)
    await user_model.save_to_state()

    return

async def withdraw_confirm_yes(callback: CallbackQuery, config: BotConfig, state: FSMContext, user_model: ModelUser, chat_id: int, message_id: int, api_client: OTPAPIClient, telegram_data: ModelTelegramData) -> None:
    if user_model.action is None or user_model.action.current_action != ACTION_WITHDRAW:
        await callback.answer("Aksi tidak valid, silahkan ulangi proses withdraw")
        await callback.message.delete()
        return

    response = await api_client.confirm_withdraw(amount=user_model.action.get_action_data(ACTION_DATA_WITHDRAW_AMOUNT), notes="")
    if response.is_error:
        user_model.add_action_message_id((await bot.send_message(chat_id, f"Gagal melakukan withdraw: {response.get_error_message()}", reply_markup=None)).message_id)
        await user_model.save_to_state()
        await callback.answer()
        return

    cached_withdraw_amounts = telegram_data.get_persistent_data(KEY_CACHED_WITHDRAW_AMOUNTS)
    if cached_withdraw_amounts is None:
        cached_withdraw_amounts = []
    if user_model.action.get_action_data(ACTION_DATA_WITHDRAW_AMOUNT) not in cached_withdraw_amounts:
        cached_withdraw_amounts.insert(0, user_model.action.get_action_data(ACTION_DATA_WITHDRAW_AMOUNT))
    if len(cached_withdraw_amounts) >= 3:
        cached_withdraw_amounts = cached_withdraw_amounts[:3]
    telegram_data.set_persistent_data(KEY_CACHED_WITHDRAW_AMOUNTS, cached_withdraw_amounts)
    await telegram_data.save_to_state()
    # await callback.message.edit_text("Withdraw berhasil, Silahkan tunggu proses withdraw selesai", reply_markup=None)
    await bot.send_message(chat_id, f"""<b>Withdraw berhasil</b>

Bank Penerima: <b>{user_model.action.get_action_data(ACTION_DATA_WITHDRAW_DESTINATION)}</b>
Jumlah Withdraw: <b>Rp.{user_model.action.get_action_data(ACTION_DATA_WITHDRAW_AMOUNT):,.0f}</b>
Silahkan tunggu proses withdraw selesai""", reply_markup=None)
    await callback.answer("Withdraw Berhasil")
    user_model.finish_action()
    await state.set_state(LoggedInStates.main_menu)
    await user_model.save_to_state()
    return

async def withdraw_cancel(callback: CallbackQuery, config: BotConfig, state: FSMContext, user_model: ModelUser, chat_id: int, message_id: int) -> None:
    if user_model.action is None or user_model.action.current_action != ACTION_WITHDRAW:
        await callback.answer()
        await callback.message.delete()
        return

    user_model.finish_action()
    await callback.answer("Proses withdraw dibatalkan")
    await user_model.save_to_state()
    return