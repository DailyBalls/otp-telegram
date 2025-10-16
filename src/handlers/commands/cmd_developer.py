from aiogram import types
from aiogram.types.inline_keyboard_button import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

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
    
async def cmd_developer_jump(msg: types.Message, config: BotConfig) -> None:
    """Process the `developer_jump` command"""
    user_id = msg.from_user.id
    if user_id not in config.whitelist_ids:
        await msg.answer(f"You are not in the whitelist")
        return

    text = msg.text.replace("/developer_jump", "").strip().split(" ")
    print(text)
    if len(text) == 0:
        await msg.answer(f"Please provide a command to jump to")
        return

    command = text[0]
    if command == "":
        await msg.answer(f"Please provide a command to jump to")
        return

    if command == "callback":
        if len(text) == 1:
            await msg.answer(f"Please provide a callback data to jump to")
            return

        callback_data = text[1]
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text=callback_data, callback_data=callback_data))
        builder.adjust(1)
        await msg.answer(f"Callback data: <b>{callback_data}</b>", reply_markup=builder.as_markup())
        return

async def cmd_developer_whoami(msg: types.Message, config: BotConfig) -> None:
    """Process the `whoami` command"""
    user_id = msg.from_user.id
    await msg.answer(f"Your user ID is {user_id}")
    return