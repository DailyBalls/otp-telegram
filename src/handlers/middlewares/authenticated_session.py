from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.types.keyboard_button import KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from handlers.callbacks.callback_auth import callback_auth_clear
from handlers.middlewares.base_model_middleware import BaseModelMiddleware
from handlers.multi import multi_menu
from handlers.multi.multi_authentication import get_guest_menu_builder
from models.model_user import ModelUser
from services.otp_services.api_client import OTPAPIClient
from services.otp_services.exceptions import InvalidSessionError
from services.otp_services.models import APIResponse
import utils.fsm as fsm_utils
from bot_instance import GuestStates, bot


class AuthenticatedSessionMiddleware(BaseModelMiddleware):
    def __init__(self) -> None:
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        self.fsm_context: FSMContext = data['state']
        self.data = data
        user_model: ModelUser | None = await self.load_model(ModelUser, 'user_model')

        api_client = OTPAPIClient(state=self.fsm_context, user_id=event.from_user.id, base_url=data['config'].otp_host)
        try:
            if user_model is None:
                raise InvalidSessionError("User model is None")

            response: APIResponse = await api_client.me()
            if response.is_authentication_error:
                if user_model:
                    await user_model.logout()
                    await user_model.delete_all_messages()
                    await user_model.delete_from_state()
                raise InvalidSessionError()
            if(response.data is None):
                print("response from OTP API is None")
                print(response, response.is_error, response.is_authentication_error, response.is_session_expired)
                return
            await user_model.fill_from_dict(response.data)
            
            if isinstance(event, CallbackQuery):
                user_model.add_message_id(event.message.message_id)
                await user_model.save_to_state()
            elif isinstance(event, Message):
                user_model.add_message_id(event.message_id)
                await user_model.save_to_state()

            data['api_client'] = api_client

            # User has already verified contact, allow request to continue
            return await handler(event, data)
        
        except InvalidSessionError as e:
            print("InvalidSessionError")
            print(e)
            if user_model:
                await user_model.logout()
                await user_model.delete_all_messages()
                await user_model.delete_from_state()

            await self.fsm_context.set_state(state=None)
            await callback_auth_clear(data['config'], self.fsm_context)
            if isinstance(event, CallbackQuery):
                await bot.send_message(event.message.chat.id, "Sesi telah berakhir, silahkan login kembali", reply_markup=get_guest_menu_builder().as_markup(resize_keyboard=True))
                await multi_menu.guest_menu(event.message, data['config'], self.fsm_context)
            else:
                await bot.send_message(event.chat.id, "Sesi telah berakhir, silahkan login kembali", reply_markup=get_guest_menu_builder().as_markup(resize_keyboard=True))
                await multi_menu.guest_menu(event, data['config'], self.fsm_context)
            return
        