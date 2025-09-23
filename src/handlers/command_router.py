from aiogram.filters import Command
from aiogram import Router

from handlers.commands.cmd_start import cmd_start
from handlers.commands.cmd_developer import cmd_developer
from handlers.middlewares.whitelisted_only import WhitelistedOnlyMiddleware

command_router = Router()
command_router.message.register(cmd_start, Command('start'))

whitelisted_only_router = Router()
whitelisted_only_router.message.middleware(WhitelistedOnlyMiddleware())
command_router.include_routers(whitelisted_only_router)

whitelisted_only_router.message.register(cmd_developer, Command('developer'))