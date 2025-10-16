from aiogram import types
from aiogram.fsm.context import FSMContext

from bot_instance import LoggedInStates
from config import BotConfig
from models.model_action import ModelAction
import utils.models as model_utils
from contextlib import suppress

async def callback_action_cancel(callback: types.CallbackQuery, config: BotConfig, state: FSMContext) -> None:
    with suppress(Exception):
        action_model: ModelAction | None = await model_utils.load_model(ModelAction, state)
        if action_model is None:
            await callback.message.delete()
            await callback.answer("Tidak ada proses yang sedang berlangsung")
            return
        
        action_model.current_action = ""

        await callback.answer("Membatalkan proses...")
        await action_model.delete_all_messages()
        await action_model.delete_from_state()
        await callback.message.delete()
        return

async def callback_action_reply_callback(callback: types.CallbackQuery, config: BotConfig, state: FSMContext) -> None:
    callback_data = callback.data.replace("action_reply_callback_", "")
    message = callback_data.replace("_", " ")
    await callback.answer(message)
    return

async def callback_action_close_with_answer(callback: types.CallbackQuery, config: BotConfig, state: FSMContext) -> None:
    callback_data = callback.data.replace("action_close_with_answer_", "")
    message = callback_data.replace("_", " ")
    await callback.answer(message)
    await callback.message.delete()
    return