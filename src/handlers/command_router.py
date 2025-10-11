from aiogram.filters import Command, Filter, and_f
from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.fsm.state import StatesGroup

from bot_instance import GuestStates, LoggedInStates
from handlers.commands.cmd_start import cmd_start, cmd_start_authenticated, cmd_start_unauthenticated
from handlers.commands.cmd_developer import cmd_developer
from handlers.commands.cmd_unbind import cmd_unbind
from handlers.middlewares.verify_contact import VerifyContactMiddleware
from handlers.middlewares.whitelisted_only import WhitelistedOnlyMiddleware
from handlers.middlewares.authenticated_session import AuthenticatedSessionMiddleware

class StatesGroup(Filter):
    def __init__(self, states_group: type[StatesGroup]):
        self.states_group = states_group

    async def __call__(self, message: Message, state: FSMContext) -> bool:
        current = await state.get_state()
        return current is not None and current.startswith(f"{self.states_group.__name__}:")

command_router = Router()
command_router.message.middleware(VerifyContactMiddleware())
# Filter for command start, but not for logged in states
command_router.message.register(cmd_start_unauthenticated, and_f(Command('start'), ~StatesGroup(LoggedInStates)))

command_router.message.register(cmd_unbind, Command('unbind'))

whitelisted_only_router = Router()
whitelisted_only_router.message.middleware(WhitelistedOnlyMiddleware())
command_router.include_routers(whitelisted_only_router)
whitelisted_only_router.message.register(cmd_developer, Command('developer'))

authenticated_only_router = Router()
authenticated_only_router.message.middleware(AuthenticatedSessionMiddleware())
command_router.include_routers(authenticated_only_router)
authenticated_only_router.message.register(cmd_start_authenticated, and_f(Command('start'), StatesGroup(LoggedInStates)))