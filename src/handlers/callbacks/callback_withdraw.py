from aiogram.fsm.context import FSMContext
from aiogram.types.callback_query import CallbackQuery

from bot_instance import LoggedInStates
from config import BotConfig
from models.model_action import ModelAction
from models.model_user import ModelUser
import utils.models as model_utils

async def callback_withdraw_init(callback: CallbackQuery, config: BotConfig, state: FSMContext, user_model: ModelUser) -> None:
    action_model: ModelAction | None = await model_utils.load_model(ModelAction, state)
    if action_model is not None:
        await action_model.finish_action()
        return
    
    action_model = ModelAction(current_action="withdraw", state=state, chat_id=callback.message.chat.id)
    await action_model.save_to_state()

    await callback.answer("Memulai proses withdraw...")
    await state.set_state(LoggedInStates.withdraw_ask_amount)
    
    reply_message = await callback.message.answer("Silahkan ketikkan jumlah withdraw, contoh: 10000")
    action_model.add_message_id(callback.message.message_id)
    action_model.add_message_id(reply_message.message_id)
    user_model.add_message_id(callback.message.message_id)
    user_model.add_message_id(reply_message.message_id)
    
    await action_model.save_to_state()
    return