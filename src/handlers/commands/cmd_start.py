from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.types.inline_keyboard_button import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import BotConfig
from models.model_user import ModelUser

async def cmd_start_unauthenticated(msg: types.Message, config: BotConfig, state: FSMContext) -> None:
    """Process the `start` command for unauthenticated users"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Login", callback_data="login"))
    builder.add(InlineKeyboardButton(text="Register", callback_data="register"))
    builder.adjust(2)  # One button per row

    await msg.answer(f"""
Halo <b>{msg.from_user.first_name}</b>!
Selamat datang di <b>{config.server_name}</b>!
Silahkan melakukan login atau register terlebih dahulu
""", reply_markup=builder.as_markup())

async def cmd_start_authenticated(msg: types.Message, config: BotConfig, state: FSMContext, user_model: ModelUser) -> None:
    """Process the `start` command for authenticated users"""

    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Deposit (On Progress)", callback_data="menu_deposit"))
    builder.add(InlineKeyboardButton(text="Withdraw (On Progress)", callback_data="menu_withdraw"))
    builder.add(InlineKeyboardButton(text="Rekening (On Progress)", callback_data="menu_rekening"))
    builder.add(InlineKeyboardButton(text="Logout", callback_data="logout"))

    play_menu_builder = InlineKeyboardBuilder()
    play_menu_builder.add(InlineKeyboardButton(text="Play Slot (On Progress)", callback_data="menu_play_slot"))
    play_menu_builder.add(InlineKeyboardButton(text="Play Casino (On Progress)", callback_data="menu_play_casino"))
    play_menu_builder.add(InlineKeyboardButton(text="Play Sports (On Progress)", callback_data="menu_play_sports"))
    play_menu_builder.add(InlineKeyboardButton(text="Play Sabung (On Progress)", callback_data="menu_play_sabung"))
    play_menu_builder.add(InlineKeyboardButton(text="Play Arcade (On Progress)", callback_data="menu_play_arcade"))
    play_menu_builder.add(InlineKeyboardButton(text="Play Interactive (On Progress)", callback_data="menu_play_interactive"))
    play_menu_builder.adjust(1)  # One button per row

    builder.attach(play_menu_builder)

    user_model.add_message_id((await msg.answer(f"""
Selamat datang di <b>{config.server_name}</b>!
Halo <b>{user_model.username}</b>!
Credit: <b>{user_model.credit}</b>
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
