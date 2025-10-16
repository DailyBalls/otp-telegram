import base64
from typing import List
from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.types.inline_keyboard_button import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import BotConfig
from models.model_games import AvailableGames, Game
from models.model_user import ModelUser
from services.otp_services.api_client import OTPAPIClient
from bot_instance import LoggedInStates, bot

async def callback_game_list(callback: types.CallbackQuery, config: BotConfig, state: FSMContext, api_client: OTPAPIClient) -> None:
    callback_data = callback.data.replace("games_list_", "").split("_")
    game_type = callback_data[0]
    page = int(callback_data[1]) if len(callback_data) > 1 else 1
    games = await api_client.list_games(game_type, page)
    is_edit_message = len(callback_data) == 2

    if games.is_error:
        await callback.answer("Gagal memuat daftar game")
        return
    
    games_list: List[Game] = []
    for game in games.data['games']:
        games_list.append(Game(**game))

    lastPage = games.data['pagination']['lastPage']
   
    builder = InlineKeyboardBuilder()
    for game in games_list:
        game_launch_string = base64.b64encode(f"{game.game_code}|{game.provider_id}".encode()).decode()
        builder.add(InlineKeyboardButton(text=game.game_name, callback_data=f"game_launch_{game_launch_string}"))
    builder.adjust(1)

    navigation_builder = InlineKeyboardBuilder()
    if page > 1:
        navigation_builder.add(InlineKeyboardButton(text="⬅️ Sebelumnya", callback_data=f"games_list_{game_type}_{page - 1}"))
    else :
        navigation_builder.add(InlineKeyboardButton(text="❌ Sebelumnya", callback_data=f"action_reply_callback_Sudah_Halaman_Pertama"))
    
    navigation_builder.add(InlineKeyboardButton(text="Tutup", callback_data=f"action_close_with_answer_"))

    if games.data['pagination']['hasMore'] == True:
        navigation_builder.add(InlineKeyboardButton(text="Selanjutnya ➡️", callback_data=f"games_list_{game_type}_{page + 1}"))
    else:
        navigation_builder.add(InlineKeyboardButton(text="Selanjutnya ❌", callback_data=f"action_reply_callback_Sudah_Halaman_Terakhir"))
    navigation_builder.adjust(3)
    builder.attach(navigation_builder)

    reply_message = f"Menampilkan Game <b>{game_type.capitalize()}</b> halaman <b>{page}/{lastPage}</b>:"
    if is_edit_message:
        await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id, text=reply_message, reply_markup=builder.as_markup())
    else:
        await callback.message.answer(text=reply_message, reply_markup=builder.as_markup())
    return

async def callback_game_generate_launch(callback: types.CallbackQuery, config: BotConfig, state: FSMContext, api_client: OTPAPIClient, user_model: ModelUser) -> None:
    game_launch_string = callback.data.replace("game_launch_", "")
    game_launch_string = base64.b64decode(game_launch_string).decode()
    game_code, provider_id = game_launch_string.split("|")
    api_response = await api_client.get_game_url(game_code, provider_id)
    if api_response.is_error:
        await callback.answer("Gagal memuat game")
        return
    # print(api_response.data)
    game_name = api_response.data['game_name']
    game_url = api_response.data['game_url']
    await callback.answer(game_name)

    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text=f"{game_name} 🔗", url=game_url))
    builder.adjust(1)
    user_model.add_message_id((await callback.message.answer("Silahkan click tombol di bawah untuk membuka game", reply_markup=builder.as_markup())).message_id)
    user_model.save_to_state()
    return

async def _game_search(user_model: ModelUser, search_base64: str, page: int, api_client: OTPAPIClient, chat_id: int, message_id: int = None) -> None:
    search_query = base64.b64decode(search_base64).decode('utf-8')
    api_response = await api_client.search_games(search_query, page)

    if api_response.is_error:
        user_model.add_message_id((await bot.send_message(chat_id=chat_id, text=api_response.get_error_message())).message_id)
        user_model.save_to_state()
        return
    
    if api_response.data['pagination']['total'] == 0:
        user_model.add_message_id((await bot.send_message(chat_id=chat_id, text=f"❌ Tidak ada game yang ditemukan dari pencarian <b>{search_query}</b>")).message_id)
        user_model.save_to_state()
        return

    games_list: List[Game] = []
    for game in api_response.data['games']:
        games_list.append(Game(**game))

    builder = InlineKeyboardBuilder()
    for game in games_list:
        game_launch_string = base64.b64encode(f"{game.game_code}|{game.provider_id}".encode('utf-8')).decode()
        builder.add(InlineKeyboardButton(text=game.game_name, callback_data=f"game_launch_{game_launch_string}"))
    builder.adjust(1)

    navigation_builder = InlineKeyboardBuilder()
    if page > 1:
        navigation_builder.add(InlineKeyboardButton(text="⬅️ Sebelumnya", callback_data=f"game_search_{page - 1}_{search_base64}"))
    else :
        navigation_builder.add(InlineKeyboardButton(text="❌ Sebelumnya", callback_data=f"action_reply_callback_Sudah_Halaman_Pertama"))
    navigation_builder.add(InlineKeyboardButton(text="Tutup", callback_data=f"action_close_with_answer_"))

    if api_response.data['pagination']['hasMore'] == True:
        navigation_builder.add(InlineKeyboardButton(text="Selanjutnya ➡️", callback_data=f"game_search_{page + 1}_{search_base64}"))
        print(f"game_search_{search_query}_{page + 1}")
    else:
        navigation_builder.add(InlineKeyboardButton(text="Selanjutnya ❌", callback_data=f"action_reply_callback_Sudah_Halaman_Terakhir"))
    navigation_builder.adjust(3)
    builder.attach(navigation_builder)

    reply_message = f"Menampilkan Game dari pencarian <b>{search_query}</b> halaman <b>{page}/{api_response.data['pagination']['lastPage']}</b>:"

    if message_id is not None:
        await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=reply_message, reply_markup=builder.as_markup())
    else:
        user_model.add_message_id((await bot.send_message(chat_id=chat_id, text=reply_message, reply_markup=builder.as_markup())).message_id)
        await user_model.save_to_state()
    return

async def callback_game_search_navigation(callback: types.CallbackQuery, config: BotConfig, state: FSMContext, api_client: OTPAPIClient, user_model: ModelUser) -> None:
    data = callback.data.replace("game_search_", "").split("_")
    page = int(data[0])
    search_base64 = data[1]
    
    await _game_search(user_model, search_base64, page, api_client, callback.message.chat.id, callback.message.message_id)
    return

async def callback_game_search_init(callback: types.CallbackQuery, config: BotConfig, state: FSMContext, api_client: OTPAPIClient, user_model: ModelUser) -> None:
    user_model.add_message_id((await callback.message.answer("Silahkan kirimkan nama atau provider game yang ingin dicari")).message_id)
    user_model.save_to_state()
    await state.set_state(LoggedInStates.game_search)
    return