from typing import List
from aiogram.types.callback_query import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.types.inline_keyboard_button import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import BotConfig
from models.model_games import Game, Provider
from models.model_user import ModelUser
from services.otp_services.api_client import OTPAPIClient
from utils.logger import get_logger
import base64
from contextlib import suppress

logger = get_logger()

async def game_list(callback: CallbackQuery, config: BotConfig, state: FSMContext, api_client: OTPAPIClient, user_model: ModelUser) -> None:
    callback_data = callback.data.replace("game_list_", "").split("_")
    game_part = callback_data[0].split("|")
    game_type = game_part[0]
    logger.debug(f"Game callback data: {callback_data}")
    provider_id = game_part[1] if len(game_part) > 1 else "all"
    page = int(callback_data[1]) if len(callback_data) > 1 else 1
    response = await api_client.list_games_by_type_and_provider(game_type, provider_id, page)
    is_edit_message = len(callback_data) == 2 or provider_id != "all"

    if response.is_error:
        await callback.answer("Gagal memuat daftar game")
        return
    
    provider_name = response.data.get('provider_name', "all")

    game_list: List[Game] = []
    for game in response.data.get('games', []):
        if game is not None: game_list.append(Game(**game))

    lastPage = response.data['pagination']['lastPage']
   
    builder = InlineKeyboardBuilder()
    for game in game_list:
        game_launch_string = base64.b64encode(f"{game.game_code}|{game.provider_id}".encode()).decode()
        builder.add(InlineKeyboardButton(text=game.game_name, callback_data=f"game_launch_{game_launch_string}"))
    builder.adjust(1)

    navigation_builder = InlineKeyboardBuilder()
    if page > 1:
        navigation_builder.add(InlineKeyboardButton(text="⬅️ Sebelumnya", callback_data=f"game_list_{callback_data[0]}_{page - 1}"))
    else :
        navigation_builder.add(InlineKeyboardButton(text="🚫 Sebelumnya", callback_data=f"action_reply_callback_Sudah_Halaman_Pertama"))
    
    navigation_builder.add(InlineKeyboardButton(text="↩️ Tutup", callback_data=f"action_close_with_answer_"))

    if response.data['pagination']['hasMore'] == True:
        navigation_builder.add(InlineKeyboardButton(text="Selanjutnya ➡️", callback_data=f"game_list_{callback_data[0]}_{page + 1}"))
    else:
        navigation_builder.add(InlineKeyboardButton(text="Selanjutnya 🚫", callback_data=f"action_reply_callback_Sudah_Halaman_Terakhir"))
    navigation_builder.adjust(3)
    builder.attach(navigation_builder)

    provider_builder = InlineKeyboardBuilder()
    provider_builder.add(InlineKeyboardButton(text="🔍 Filter Berdasarkan Provider 🔍", callback_data=f"game_provider_list_{game_type}"))
    provider_builder.adjust(1)

    builder.attach(provider_builder)


    reply_message = f"Menampilkan Game <b>{game_type.capitalize()}</b> untuk semua provider.\nhalaman <b>{page}/{lastPage}</b>:"
    if provider_name != "all":
        reply_message = f"Menampilkan Game <b>{game_type.capitalize()}</b> untuk provider <b>{provider_name}</b>. \nMenampilkan halaman <b>{page}/{lastPage}</b>:"

    if is_edit_message:
        with suppress(Exception):
            await callback.message.edit_text(text=reply_message, reply_markup=builder.as_markup())
    else:
        user_model.add_message_id((await callback.message.answer(text=reply_message, reply_markup=builder.as_markup())).message_id)

    await callback.answer(f"Menampilkan Halaman {page}/{lastPage}")
    return

async def game_provider_list(callback: CallbackQuery, config: BotConfig, state: FSMContext, api_client: OTPAPIClient, user_model: ModelUser) -> None:
    callback_data = callback.data.replace("game_provider_list_", "")
    game_type = callback_data
    providers = await api_client.list_providers(game_type)
    if providers.is_error:
        await callback.answer("Gagal memuat daftar provider")
        return
    providers_list: List[Provider] = []
    for provider in providers.data.get('providers', []):
        if provider is not None: providers_list.append(Provider(**provider))
    builder = InlineKeyboardBuilder()
    for provider in providers_list:
        builder.add(InlineKeyboardButton(text=f"{provider.provider_name_mobile}", callback_data=f"game_list_{game_type}|{provider.provider_id}"))
    builder.adjust(2)
    navigation_builder = InlineKeyboardBuilder()
    navigation_builder.add(InlineKeyboardButton(text="🔙 Kembali", callback_data=f"game_list_{game_type}_1"))
    navigation_builder.add(InlineKeyboardButton(text="↩️ Tutup", callback_data=f"action_close_with_answer_"))
    navigation_builder.adjust(2)
    builder.attach(navigation_builder)
    await callback.message.edit_text(text=f"Menampilkan list provider untuk game <b>{game_type.capitalize()}</b>:", reply_markup=builder.as_markup())
    return
    