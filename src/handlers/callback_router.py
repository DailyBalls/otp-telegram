from aiogram import Router
from aiogram import F 
from aiogram.filters import Filter, MagicData
from aiogram.types import Message
from aiogram.types.callback_query import CallbackQuery

from handlers.callbacks.callback_action import callback_action_cancel, callback_action_reply_callback, callback_action_close_with_answer
from handlers.callbacks.callback_deposit import callback_deposit_ask_payment_method, callback_deposit_confirm_channel, callback_deposit_init, callback_deposit_ask_channel, callback_deposit_confirm_yes
from handlers.callbacks.callback_game import callback_game_generate_launch, callback_game_list, callback_game_search_init, callback_game_search_navigation
from handlers.callbacks.callback_logout import callback_logout
from handlers.callbacks.callback_login import callback_login
from handlers.callbacks.callback_register import callback_register_init, callback_register_bank, callback_register_edit, callback_auth_clear, callback_register_confirm_yes, callback_register_confirm_no
from handlers.callbacks.callback_rekening import callback_rekening_list
from handlers.middlewares.register_middleware import RegisterSessionMiddleware
from handlers.middlewares.authenticated_session import AuthenticatedSessionMiddleware
from utils.filters import Text, TextPrefix


callback_router = Router()
callback_router.callback_query.register(callback_register_init, Text(data="register"))
callback_router.callback_query.register(callback_logout, Text(data="logout"))
callback_router.callback_query.register(callback_login, Text(data="login"))

register_router = Router()
register_router.callback_query.middleware(RegisterSessionMiddleware())
register_router.callback_query.register(callback_auth_clear, Text(data="auth_cancel"))
register_router.callback_query.register(callback_register_edit, TextPrefix(prefix="register_edit_"))
register_router.callback_query.register(callback_register_bank, TextPrefix(prefix="register_bank_"))
register_router.callback_query.register(callback_register_confirm_yes, Text(data="register_confirm_yes"))
register_router.callback_query.register(callback_auth_clear, Text(data="register_confirm_no"))
callback_router.include_router(register_router)

logged_in_router = Router()
logged_in_router.callback_query.middleware(AuthenticatedSessionMiddleware())
# Deposit callbacks
logged_in_router.callback_query.register(callback_deposit_init, Text(data="deposit_init"))
logged_in_router.callback_query.register(callback_deposit_ask_payment_method, TextPrefix(prefix="deposit_ask_method_"))
logged_in_router.callback_query.register(callback_deposit_ask_channel, TextPrefix(prefix="deposit_ask_channel_"))
logged_in_router.callback_query.register(callback_deposit_confirm_channel, TextPrefix(prefix="deposit_confirm_channel_"))
logged_in_router.callback_query.register(callback_deposit_confirm_yes, TextPrefix(prefix="deposit_confirm_yes_"))
logged_in_router.callback_query.register(callback_action_cancel, TextPrefix(prefix="deposit_confirm_no_"))
logged_in_router.callback_query.register(callback_action_cancel, Text(data="action_cancel"))

# Games callbacks
logged_in_router.callback_query.register(callback_game_list, TextPrefix(prefix="games_list_"))
logged_in_router.callback_query.register(callback_game_generate_launch, TextPrefix(prefix="game_launch_"))
logged_in_router.callback_query.register(callback_game_search_init, Text(data="game_search_init"))
logged_in_router.callback_query.register(callback_game_search_navigation, TextPrefix(prefix="game_search_"))

# Rekening callbacks
logged_in_router.callback_query.register(callback_rekening_list, Text(data="rekening_list"))

# Action callbacks
callback_router.callback_query.register(callback_action_reply_callback, TextPrefix(prefix="action_reply_callback_"))
callback_router.callback_query.register(callback_action_close_with_answer, TextPrefix(prefix="action_close_with_answer_"))

callback_router.include_router(logged_in_router)
# logged_in_router.callback_query.register(callback_deposit_ask_pg_channel, TextPrefix(prefix="deposit_ask_pg_channel_"))
