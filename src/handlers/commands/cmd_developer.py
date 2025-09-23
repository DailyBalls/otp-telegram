from aiogram import types

from config import BotConfig

async def cmd_developer(msg: types.Message, config: BotConfig) -> None:
    """Process the `developer` command"""
    user_id = msg.from_user.id
   
    await msg.answer(
f"""<b>Developer mode</b>
<b>Whitelist Mode:</b> {config.whitelist_mode}
<b>Server name:</b> {config.server_name}
<b>Your User ID:</b> {user_id}
<b>Whitelist IDs:</b> {config.whitelist_ids}
<b>Is Whitelisted:</b> {user_id in config.whitelist_ids}
"""
    )
    
