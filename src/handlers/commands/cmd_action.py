from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.types.callback_query import CallbackQuery
from aiogram.types.inline_keyboard_button import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot_instance import bot
from config import BotConfig
from models.model_user import ModelUser
import utils.models as model_utils

async def cmd_start_unauthenticated(msg: types.Message, config: BotConfig, state: FSMContext) -> None:
    """Process the `start` command for unauthenticated users"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Login", callback_data="login"))
    builder.add(InlineKeyboardButton(text="Register", callback_data="register"))
    builder.adjust(2)  # One button per row
    if isinstance(msg, CallbackQuery):
        chat_id = msg.message.chat.id
    else:
        chat_id = msg.chat.id
        
    await bot.send_message(chat_id, f"""
Halo <b>{msg.from_user.first_name}</b>!
Selamat datang di <b>{config.server_name}</b>!
Silahkan melakukan login atau register terlebih dahulu
""", reply_markup=builder.as_markup())

async def cmd_start_authenticated(msg: types.Message, config: BotConfig, state: FSMContext, user_model: ModelUser) -> None:
    """Process the `start` command for authenticated users"""

    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="💲Deposit", callback_data="deposit_init"))
    builder.add(InlineKeyboardButton(text="💰Withdraw", callback_data="menu_withdraw"))
    builder.add(InlineKeyboardButton(text="💳Rekening", callback_data="rekening_list"))
    builder.add(InlineKeyboardButton(text="↩️Logout", callback_data="logout"))
    builder.adjust(2)

    play_menu_builder = InlineKeyboardBuilder()
    play_menu_builder.add(InlineKeyboardButton(text="🎰 Play Slot 🎰", callback_data="games_list_slot"))
    play_menu_builder.add(InlineKeyboardButton(text="♠️ Play Casino ♠️", callback_data="games_list_casino"))
    play_menu_builder.add(InlineKeyboardButton(text="🏈 Play Sports 🏈", callback_data="games_list_sports"))
    play_menu_builder.add(InlineKeyboardButton(text="🐔 Play Sabung 🐔", callback_data="games_list_sabung"))
    play_menu_builder.add(InlineKeyboardButton(text="🕹️ Play Arcade 🕹️", callback_data="games_list_arcade"))
    play_menu_builder.add(InlineKeyboardButton(text="🎬 Play Interactive 🎬", callback_data="games_list_interactive"))
    play_menu_builder.add(InlineKeyboardButton(text="🔎 Search Game 🔎", callback_data="game_search_init"))
    play_menu_builder.adjust(1)  # One button per row

    builder.attach(play_menu_builder)

    user_model.add_message_id((await msg.answer(f"""
Selamat datang di <b>{config.server_name}</b>!
Halo <b>{user_model.username}</b>!
Credit: <b>Rp {float(user_model.credit):,.0f}</b>
Rank: <b>{user_model.rank}</b>

Silahkan pilih menu yang tersedia
""", reply_markup=builder.as_markup())).message_id)

async def cmd_start(msg: types.Message, config: BotConfig, state: FSMContext) -> None:
    """Process the `start` command"""
    user_model = ModelUser()
    user_model._state = state
    state_key = user_model._get_state_key()
    user_data = await state.get_data()
    user_data = user_data.get(state_key, False)
    if user_data:
        user_model = ModelUser.model_validate_json(user_data)
        user_model._state = state
        return await cmd_start_authenticated(msg, config, state, user_model)
    else:
        return await cmd_start_unauthenticated(msg, config, state)

async def cmd_stop(msg: types.Message, config: BotConfig, state: FSMContext) -> None:
    """Process the `stop` command"""
    user_model = await model_utils.load_model(ModelUser, state)
    if state.get_state() is not None:
        await msg.answer("Bot stopped")
        await state.clear()
    return