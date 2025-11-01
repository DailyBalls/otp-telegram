import base64
from contextlib import suppress
from typing import List
from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.types.inline_keyboard_button import InlineKeyboardButton
from aiogram.types.web_app_info import WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import BotConfig
from models.model_games import Game, Provider
from models.model_user import ModelUser
from services.otp_services.api_client import OTPAPIClient
from bot_instance import LoggedInStates, bot
from utils.logger import get_logger

logger = get_logger()

async def callback_game_generate_launch(callback: types.CallbackQuery, config: BotConfig, state: FSMContext, api_client: OTPAPIClient, user_model: ModelUser) -> None:
    game_launch_string = callback.data.replace("game_launch_", "")
    game_launch_string = base64.b64decode(game_launch_string).decode()
    game_code, provider_id = game_launch_string.split("|")
    api_response = await api_client.get_game_url(game_code, provider_id)
    if api_response.is_error:
        await callback.answer(f"Gagal memuat game: {api_response.get_error_message()}")
        return
    # print(api_response.data)
    game_name = api_response.data['game_name']
    game_url = api_response.data['game_url']
    image_url = api_response.data['image_url']
    await callback.answer(game_name)


    builder = InlineKeyboardBuilder()
    web_app = WebAppInfo(url=game_url)
    builder.add(InlineKeyboardButton(text=f"Buka Game 🔗", web_app=web_app))
    builder.add(InlineKeyboardButton(text="↩️ Tutup", callback_data=f"action_close_with_answer_"))
    builder.adjust(2)
    if image_url is not None:
        user_model.add_message_id((await callback.message.answer_photo(caption=game_name, photo=image_url, reply_markup=builder.as_markup())).message_id)
    else:
        user_model.add_message_id((await callback.message.answer(f"{game_name}\n\nSilahkan click tombol di bawah untuk membuka game", reply_markup=builder.as_markup())).message_id)
    await user_model.save_to_state()
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

    game_list: List[Game] = []
    for game in api_response.data['games']:
        game_list.append(Game(**game))

    builder = InlineKeyboardBuilder()
    for game in game_list:
        game_launch_string = base64.b64encode(f"{game.game_code}|{game.provider_id}".encode('utf-8')).decode()
        builder.add(InlineKeyboardButton(text=game.game_name, callback_data=f"game_launch_{game_launch_string}"))
    builder.adjust(1)

    navigation_builder = InlineKeyboardBuilder()
    if page > 1:
        navigation_builder.add(InlineKeyboardButton(text="⬅️ Sebelumnya", callback_data=f"game_search_{page - 1}_{search_base64}"))
    else :
        navigation_builder.add(InlineKeyboardButton(text="🚫 Sebelumnya", callback_data=f"action_reply_callback_Sudah_Halaman_Pertama"))
    navigation_builder.add(InlineKeyboardButton(text="↩️ Tutup", callback_data=f"action_close_with_answer_"))

    if api_response.data['pagination']['hasMore'] == True:
        callback_data_str = f"game_search_{search_query}_{page + 1}"
        logger.debug(f"Game search callback data: {callback_data_str}")
        navigation_builder.add(InlineKeyboardButton(text="Selanjutnya ➡️", callback_data=f"game_search_{page + 1}_{search_base64}"))
    else:
        navigation_builder.add(InlineKeyboardButton(text="Selanjutnya 🚫", callback_data=f"action_reply_callback_Sudah_Halaman_Terakhir"))
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
    if data[0] == "cancel":
        await callback.answer("Pencarian game dibatalkan")
        await callback.message.delete()
        await state.set_state(LoggedInStates.main_menu)
        return
    page = int(data[0])
    search_base64 = data[1]
    
    await _game_search(user_model, search_base64, page, api_client, callback.message.chat.id, callback.message.message_id)
    return

async def callback_game_search_init(callback: types.CallbackQuery, config: BotConfig, state: FSMContext, api_client: OTPAPIClient, user_model: ModelUser) -> None:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="❌ Batalkan", callback_data=f"game_search_cancel"))
    builder.adjust(1)
    user_model.add_message_id((await callback.message.answer("Silahkan kirimkan nama atau provider game yang ingin dicari", reply_markup=builder.as_markup())).message_id)
    await user_model.save_to_state()
    await state.set_state(LoggedInStates.game_search)
    return