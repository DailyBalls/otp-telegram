from aiogram import Router
from aiogram import F 
from aiogram.filters import Filter, MagicData
from aiogram.types import Message
from aiogram.types.callback_query import CallbackQuery

from handlers.callbacks.callback_action import callback_action_cancel, callback_action_reply_callback, callback_action_close_with_answer
from handlers.callbacks.callback_deposit import callback_deposit_ask_payment_method, callback_deposit_confirm_channel, callback_deposit_init, callback_deposit_ask_channel, callback_deposit_confirm_yes, callback_deposit_cancel
from handlers.callbacks.callback_game import callback_game_generate_launch, callback_game_search_init, callback_game_search_navigation
from handlers.callbacks.callback_register import callback_register_bank, callback_register_edit, callback_auth_clear, callback_register_confirm_yes
from handlers.callbacks.callback_rekening import callback_rekening_add, callback_rekening_list, callback_rekening_add_bank, callback_rekening_add_cancel, callback_rekening_add_confirm
from handlers.middlewares.register_middleware import RegisterSessionMiddleware
from handlers.middlewares.authenticated_session import AuthenticatedSessionMiddleware
from handlers.middlewares.verify_private_chat import VerifyPrivateChatMiddleware
from utils.filters import Text, TextPrefix
from handlers.middlewares.verify_contact import VerifyContactMiddleware
from handlers.multi import multi_authentication, multi_game, multi_menu, multi_transaction, multi_withdraw, multi_deposit


callback_router = Router()
callback_router.callback_query.middleware(VerifyPrivateChatMiddleware())
callback_router.callback_query.middleware(VerifyContactMiddleware())
callback_router.callback_query.register(multi_authentication.register_init, Text(data="register"))
callback_router.callback_query.register(multi_authentication.register_cancel, Text(data="register_cancel"))
callback_router.callback_query.register(multi_authentication.logout, Text(data="logout"))
callback_router.callback_query.register(multi_authentication.login_init, Text(data="login"))
callback_router.callback_query.register(multi_authentication.login_cancel, Text(data="login_cancel"))

register_router = Router()
register_router.callback_query.middleware(RegisterSessionMiddleware())
register_router.callback_query.register(callback_register_edit, TextPrefix(prefix="register_edit_"))
register_router.callback_query.register(callback_register_bank, TextPrefix(prefix="register_bank_"))
register_router.callback_query.register(callback_register_confirm_yes, Text(data="register_confirm_yes"))
register_router.callback_query.register(callback_auth_clear, Text(data="register_confirm_no"))
callback_router.include_router(register_router)

logged_in_router = Router()
logged_in_router.callback_query.middleware(AuthenticatedSessionMiddleware())

# Menu callbacks
logged_in_router.callback_query.register(multi_menu.social_media_menu, Text(data="menu_social_media"))
logged_in_router.callback_query.register(multi_transaction.transaction_history, Text(data="transaction_history"))

# Deposit callbacks
logged_in_router.callback_query.register(multi_deposit.deposit_init, Text(data="deposit_init"))
logged_in_router.callback_query.register(multi_deposit.deposit_ask_method, Text(data="deposit_ask_method"))
logged_in_router.callback_query.register(multi_deposit.deposit_submit_amount, TextPrefix(prefix="deposit_submit_amount_"))
logged_in_router.callback_query.register(multi_deposit.deposit_channel, TextPrefix(prefix="deposit_channel_"))
logged_in_router.callback_query.register(multi_deposit.deposit_submit_method, TextPrefix(prefix="deposit_submit_method_"))
logged_in_router.callback_query.register(multi_deposit.deposit_ask_channel, Text(data="deposit_ask_channel"))
logged_in_router.callback_query.register(multi_deposit.deposit_ask_user_bank, Text(data="deposit_ask_user_bank"))
logged_in_router.callback_query.register(multi_deposit.deposit_choose_user_bank, TextPrefix(prefix="deposit_choose_user_bank_"))
logged_in_router.callback_query.register(multi_deposit.deposit_confirm_promo, TextPrefix(prefix="deposit_confirm_promo_"))
logged_in_router.callback_query.register(multi_deposit.deposit_choose_promo, TextPrefix(prefix="deposit_choose_promo_"))
logged_in_router.callback_query.register(multi_deposit.deposit_submit_note, Text(data="deposit_submit_note"))
logged_in_router.callback_query.register(multi_deposit.deposit_confirm_submit, Text(data="deposit_confirm_submit"))
logged_in_router.callback_query.register(multi_deposit.deposit_confirm_submit, Text(data="deposit_confirm_submit_retry"))
logged_in_router.callback_query.register(callback_deposit_confirm_channel, TextPrefix(prefix="deposit_confirm_channel_"))
logged_in_router.callback_query.register(callback_deposit_confirm_yes, TextPrefix(prefix="deposit_confirm_yes_"))
logged_in_router.callback_query.register(multi_deposit.deposit_cancel, Text(data="deposit_cancel"))
logged_in_router.callback_query.register(callback_deposit_cancel, TextPrefix(prefix="deposit_confirm_no_"))
logged_in_router.callback_query.register(multi_deposit.deposit_back_button, TextPrefix(prefix="deposit_back_button_"))
# Withdraw callbacks
logged_in_router.callback_query.register(multi_withdraw.withdraw_init, Text(data="withdraw_init"))
logged_in_router.callback_query.register(multi_withdraw.withdraw_input_amount, TextPrefix(prefix="withdraw_amount_"))
logged_in_router.callback_query.register(multi_withdraw.withdraw_confirm_yes, Text(data="withdraw_confirm_yes"))
logged_in_router.callback_query.register(multi_withdraw.withdraw_cancel, Text(data="withdraw_cancel"))
# logged_in_router.callback_query.register(callback_withdraw_ask_amount, TextPrefix(prefix="withdraw_ask_amount_"))
# logged_in_router.callback_query.register(callback_withdraw_ask_confirm, TextPrefix(prefix="withdraw_ask_confirm_"))
# logged_in_router.callback_query.register(callback_withdraw_ask_notes, TextPrefix(prefix="withdraw_ask_notes_"))
# logged_in_router.callback_query.register(callback_withdraw_cancel, Text(data="withdraw_cancel"))
logged_in_router.callback_query.register(callback_action_cancel, Text(data="action_cancel"))

# Games callbacks
logged_in_router.callback_query.register(multi_game.game_list, TextPrefix(prefix="game_list_"))
logged_in_router.callback_query.register(callback_game_generate_launch, TextPrefix(prefix="game_launch_"))
logged_in_router.callback_query.register(callback_game_search_init, Text(data="game_search_init"))
logged_in_router.callback_query.register(callback_game_search_navigation, TextPrefix(prefix="game_search_"))
logged_in_router.callback_query.register(multi_game.game_provider_list, TextPrefix(prefix="game_provider_list_"))
# Rekening callbacks
logged_in_router.callback_query.register(callback_rekening_list, Text(data="rekening_list"))
logged_in_router.callback_query.register(callback_rekening_add, Text(data="rekening_add"))
logged_in_router.callback_query.register(callback_rekening_add_bank, TextPrefix(prefix="rekening_add_bank_"))
logged_in_router.callback_query.register(callback_rekening_add_cancel, Text(data="rekening_add_cancel"))
logged_in_router.callback_query.register(callback_rekening_add_confirm, Text(data="rekening_add_confirm"))
# Action callbacks
callback_router.callback_query.register(callback_action_reply_callback, TextPrefix(prefix="action_reply_callback_"))
callback_router.callback_query.register(callback_action_close_with_answer, TextPrefix(prefix="action_close_with_answer_"))

callback_router.include_router(logged_in_router)
# logged_in_router.callback_query.register(callback_deposit_ask_pg_channel, TextPrefix(prefix="deposit_ask_pg_channel_"))
