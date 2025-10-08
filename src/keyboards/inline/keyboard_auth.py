from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def registration_confirm_and_edit() -> InlineKeyboardBuilder:
    builder_confirm = InlineKeyboardBuilder()
    builder_confirm.add(InlineKeyboardButton(text="Ya", callback_data="register_confirm_yes"))
    builder_confirm.add(InlineKeyboardButton(text="Batalkan", callback_data="auth_cancel"))
    builder_confirm.adjust(2)

    builder_edit = InlineKeyboardBuilder()
    builder_edit.add(InlineKeyboardButton(text="Edit Username", callback_data="register_edit_username"))
    builder_edit.add(InlineKeyboardButton(text="Edit Password", callback_data="register_edit_password"))
    builder_edit.add(InlineKeyboardButton(text="Edit Bank", callback_data="register_edit_bank"))
    builder_edit.add(InlineKeyboardButton(text="Edit Nama Rekening", callback_data="register_edit_bank_account_name"))
    builder_edit.add(InlineKeyboardButton(text="Edit Nomor Rekening", callback_data="register_edit_bank_account_number"))
    builder_edit.adjust(1)

    builder_confirm.attach(builder_edit)

    return builder_confirm

def bank_selection(bank_list: list[str]) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    for bank in bank_list:
        builder.add(InlineKeyboardButton(text=bank, callback_data=f"register_bank_{bank}"))
    builder.adjust(2)
    builder.add(InlineKeyboardButton(text="Batalkan", callback_data="auth_cancel"))
    return builder

def auth_cancel() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Batalkan", callback_data="auth_cancel"))
    return builder