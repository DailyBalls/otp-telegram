from aiogram.filters import Command, Filter, and_f
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot_instance import GuestStates, LoggedInStates
from handlers.commands.cmd_developer import cmd_developer, cmd_developer_jump, cmd_developer_whoami
from handlers.commands.cmd_unbind import cmd_unbind
from handlers.middlewares.verify_contact import VerifyContactMiddleware
from handlers.middlewares.whitelisted_only import WhitelistedOnlyMiddleware
from handlers.middlewares.authenticated_session import AuthenticatedSessionMiddleware
from handlers.multi import multi_login, multi_register, multi_menu
from utils.filters import StatesGroup
from handlers.middlewares.verify_private_chat import VerifyPrivateChatMiddleware


command_router = Router()
command_router.message.middleware(VerifyPrivateChatMiddleware())
command_router.message.filter(F.text.startswith("/"))
command_router.message.middleware(VerifyContactMiddleware())

# This should be keep in Global command_router
# it should be accessible in any states of user

command_router.message.register(multi_login.logout, Command('logout'))
command_router.message.register(cmd_developer_whoami, Command('whoami'))
command_router.message.register(cmd_unbind, Command('unbind'))

# Filter this Command only accessible for Guest only!
guest_only_router = Router()
guest_only_router.message.filter(~StatesGroup(LoggedInStates)) # ~ = Not in LoggedInStates
guest_only_router.message.register(multi_menu.guest_menu, Command('start'))
guest_only_router.message.register(multi_menu.guest_menu, Command('menu'))
guest_only_router.message.register(multi_login.login_init, Command('login'))
guest_only_router.message.register(multi_register.register_init, Command('register'))
command_router.include_routers(guest_only_router)


developer_only_router = Router()
developer_only_router.message.middleware(WhitelistedOnlyMiddleware())
developer_only_router.message.register(cmd_developer, Command('developer'))
developer_only_router.message.register(cmd_developer_jump, Command('developer_jump'))
command_router.include_routers(developer_only_router)

authenticated_only_router = Router()
authenticated_only_router.message.filter(StatesGroup(LoggedInStates))
authenticated_only_router.message.middleware(AuthenticatedSessionMiddleware())
authenticated_only_router.message.register(multi_menu.logged_in_menu, Command('start'))
authenticated_only_router.message.register(multi_menu.logged_in_menu, Command('menu'))
authenticated_only_router.message.register(multi_login.logout, Command('logout'))
command_router.include_routers(authenticated_only_router)
# authenticated_only_router.message.register(cmd_stop, Command('stop'))