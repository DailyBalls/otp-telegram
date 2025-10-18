from aiogram.filters import Command, Filter, and_f
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot_instance import GuestStates, LoggedInStates
from handlers.commands.cmd_action import cmd_start, cmd_start_authenticated, cmd_start_unauthenticated, cmd_stop
from handlers.commands.cmd_developer import cmd_developer, cmd_developer_jump, cmd_developer_whoami
from handlers.commands.cmd_unbind import cmd_unbind
from handlers.middlewares.verify_contact import VerifyContactMiddleware
from handlers.middlewares.whitelisted_only import WhitelistedOnlyMiddleware
from handlers.middlewares.authenticated_session import AuthenticatedSessionMiddleware
from handlers.multi import multi_authentication
from utils.filters import StatesGroup
from handlers.middlewares.verify_private_chat import VerifyPrivateChatMiddleware


command_router = Router()
command_router.message.middleware(VerifyPrivateChatMiddleware())
command_router.message.filter(F.text.startswith("/"))
command_router.message.middleware(VerifyContactMiddleware())
command_router.message.register(multi_authentication.logout, Command('logout'))
command_router.message.register(multi_authentication.login_init, Command('login'))
command_router.message.register(multi_authentication.register_init, Command('register'))

# Filter for command start, but not for logged in states
command_router.message.register(cmd_start_unauthenticated, and_f(Command('start'), ~StatesGroup(LoggedInStates)))
command_router.message.register(cmd_developer_whoami, Command('whoami'))
command_router.message.register(cmd_unbind, Command('unbind'))

developer_only_router = Router()
developer_only_router.message.middleware(WhitelistedOnlyMiddleware())
command_router.include_routers(developer_only_router)
developer_only_router.message.register(cmd_developer, Command('developer'))
developer_only_router.message.register(cmd_developer_jump, Command('developer_jump'))

authenticated_only_router = Router()
authenticated_only_router.message.middleware(AuthenticatedSessionMiddleware())
command_router.include_routers(authenticated_only_router)
authenticated_only_router.message.register(cmd_stop, Command('stop'))