from bot_instance import bot

async def delete_messages(chat_id: int, messages_ids: list[int]) -> None:  
    try:
       await bot.delete_messages(chat_id, messages_ids)
    except Exception as e:
        print(e)
        pass
    