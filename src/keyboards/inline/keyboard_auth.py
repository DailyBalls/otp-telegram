from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def action_cancel() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="❌ Batalkan", callback_data="action_cancel"))
    return builder