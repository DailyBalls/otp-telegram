from bot_instance import bot
from utils.logger import get_logger

logger = get_logger()

async def delete_messages(chat_id: int, messages_ids: list[int]) -> None:  
    try:
       await bot.delete_messages(chat_id, messages_ids)
    except Exception as e:
        logger.error(f"Error deleting messages: {e}")
        pass
    