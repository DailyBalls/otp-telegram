from aiogram.filters import Filter 
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram import Bot, types
from os import getenv
from aiogram.client.default import DefaultBotProperties

from aiogram.fsm.state import State, StatesGroup

class StatesGroup(Filter):
    def __init__(self, states_group: type[StatesGroup]):
        self.states_group = states_group

    async def __call__(self, message: Message, state: FSMContext) -> bool:
        current = await state.get_state()
        return current is not None and current.startswith(f"{self.states_group.__name__}:")


class Text(Filter):
    def __init__(self, data: str) -> None:
        self.data = data

    async def __call__(self, callback: CallbackQuery | Message) -> bool:
        if isinstance(callback, CallbackQuery):
            return callback.data == self.data
        elif isinstance(callback, Message):
            return callback.text.lower() == self.data.lower()

class TextPrefix(Filter):
    def __init__(self, prefix: str) -> None:
        self.prefix = prefix

    async def __call__(self, callback: CallbackQuery) -> bool:
        return callback.data.startswith(self.prefix)
