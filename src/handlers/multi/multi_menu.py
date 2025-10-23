from aiogram.types import InlineKeyboardButton, Message
from aiogram.fsm.context import FSMContext
from aiogram.types.callback_query import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot_instance import LoggedInStates, bot
from config import BotConfig
from models.model_menu import ModelMenu
from models.model_user import ModelUser
import utils.models as model_utils

'''
Multi Menu Main Function

Entrypoint:
- Message Router (text: Menu)
- Command Router (cmd: menu)
- Command Router (cmd: start)
'''
async def logged_in_menu(msg: Message, config: BotConfig, state: FSMContext, user_model: ModelUser) -> None:
    menu_model: ModelMenu | None = await model_utils.load_model(ModelMenu, state)
    if menu_model is None:
        menu_model = ModelMenu(state=state, chat_id=msg.chat.id, logged_in=True)

    if menu_model.logged_in == False:
        await menu_model.delete_all_messages()
    
    if menu_model.list_menu_ids is not None and len(menu_model.list_menu_ids) > 2:
        await menu_model.delete_first_menu()

    await state.set_state(LoggedInStates.main_menu)

    # print(menu_model.list_menu_ids)
    menu_model.add_message_id(msg.message_id)
    menu_model.logged_in = True
    
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="💲Deposit", callback_data="deposit_init"))
    if user_model.pending_wd == False:
        builder.add(InlineKeyboardButton(text="💰Withdraw", callback_data="withdraw_init"))
    else:
        builder.add(InlineKeyboardButton(text="🚧𝚆̶𝚒̶𝚝̶𝚑̶𝚍̶𝚛̶𝚊̶𝚠̶", callback_data="withdraw_init"))
    builder.add(InlineKeyboardButton(text="💳Rekening", callback_data="rekening_list"))
    builder.add(InlineKeyboardButton(text="↩️Logout", callback_data="logout"))
    builder.adjust(2)

    play_menu_builder = InlineKeyboardBuilder()
    # play_menu_builder.add(InlineKeyboardButton(text="🎰 Play Slot 🎰", callback_data="games_list_slot"))
    # play_menu_builder.add(InlineKeyboardButton(text="♠️ Play Casino ♠️", callback_data="games_list_casino"))
    # play_menu_builder.add(InlineKeyboardButton(text="🏈 Play Sports 🏈", callback_data="games_list_sports"))
    # play_menu_builder.add(InlineKeyboardButton(text="🐔 Play Sabung 🐔", callback_data="games_list_sabung"))
    # play_menu_builder.add(InlineKeyboardButton(text="🕹️ Play Arcade 🕹️", callback_data="games_list_arcade"))
    # play_menu_builder.add(InlineKeyboardButton(text="🎬 Play Interactive 🎬", callback_data="games_list_interactive"))
    # play_menu_builder.add(InlineKeyboardButton(text="🔎 Search Game 🔎", callback_data="game_search_init"))
    play_menu_builder.add(InlineKeyboardButton(text="🎰 Play Slot 🎰", callback_data="provider_list_slot"))
    play_menu_builder.add(InlineKeyboardButton(text="♠️ Play Casino ♠️", callback_data="provider_list_casino"))
    play_menu_builder.add(InlineKeyboardButton(text="🏈 Play Sports 🏈", callback_data="provider_list_sports"))
    play_menu_builder.add(InlineKeyboardButton(text="🐔 Play Sabung 🐔", callback_data="provider_list_sabung"))
    play_menu_builder.add(InlineKeyboardButton(text="🕹️ Play Arcade 🕹️", callback_data="provider_list_arcade"))
    play_menu_builder.add(InlineKeyboardButton(text="🎬 Play Interactive 🎬", callback_data="provider_list_interactive"))
    play_menu_builder.add(InlineKeyboardButton(text="🔎 Search Game 🔎", callback_data="game_search_init"))
    play_menu_builder.adjust(1)  # One button per row

    builder.attach(play_menu_builder)

    menu_id = (await msg.answer(f"""
Selamat datang di <b>{config.server_name}</b>!
Halo <b>{user_model.username}</b>!
Credit: <b>Rp {float(user_model.credit):,.0f}</b>
Rank: <b>{user_model.rank}</b>

Silahkan pilih menu yang tersedia
""", reply_markup=builder.as_markup())).message_id

    menu_model.add_menu_id(menu_id)
    user_model.add_message_id(menu_id)
    await user_model.save_to_state()
    await menu_model.save_to_state()

'''
Guest Menu

Entrypoint:
- Message Router (text: Menu)
- Command Router (cmd: menu)
- Command Router (cmd: start)
'''
async def guest_menu(msg: Message, config: BotConfig, state: FSMContext) -> None:
    menu_model: ModelMenu | None = await model_utils.load_model(ModelMenu, state)
    if menu_model is None:
        menu_model = ModelMenu(state=state, chat_id=msg.chat.id, logged_in=False, list_message_ids=[], list_menu_ids=[])

    if menu_model.logged_in == True:
        await menu_model.delete_all_messages()

    if menu_model.list_menu_ids is not None and len(menu_model.list_menu_ids) > 5:
        await menu_model.delete_first_menu()

    menu_model.add_message_id(msg.message_id)
    menu_model.logged_in=False
    print(menu_model.list_menu_ids)
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Login", callback_data="login"))
    builder.add(InlineKeyboardButton(text="Register", callback_data="register"))
    builder.adjust(2)  # One button per row

    menu_id = (await bot.send_message(msg.chat.id, f"""
Halo <b>{msg.from_user.first_name}</b>!
Selamat datang di <b>{config.server_name}</b>!
Silahkan melakukan login atau register terlebih dahulu
""", reply_markup=builder.as_markup())).message_id

    menu_model.add_menu_id(menu_id)
    await menu_model.save_to_state()