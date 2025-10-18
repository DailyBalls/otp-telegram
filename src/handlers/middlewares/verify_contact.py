from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Contact, KeyboardButton, Message
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from handlers.middlewares.base_model_middleware import BaseModelMiddleware
from models.model_telegram_data import ModelTelegramData
import utils.models as model_utils

class VerifyContactMiddleware(BaseModelMiddleware):
    def __init__(self) -> None:
        pass

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        self.fsm_context = data['state']
        self.data = data
        
        telegram_data_model = await self.load_model(ModelTelegramData, 'telegram_data')
        
        if telegram_data_model is not None and telegram_data_model.contact_verified:
            # User has already verified contact, allow request to continue
            print(data['config'])
            return await handler(event, data)
        
        contact: Contact | None = None

        if isinstance(event, CallbackQuery): # If the event is a callback query, get the message
            event = event.message
        elif isinstance(event, Message): # If the event is a message, get the contact
            contact = event.contact
            
        if contact is None:
            markup = ReplyKeyboardBuilder()
            b5 = KeyboardButton(text="Verifikasi Akun", request_contact=True)
            markup.add(b5)
            await event.answer(
                "🔐 <b>Verifikasi Diperlukan</b>\n\n"
                "Untuk menghindari penggunaan yang tidak sah, Silahkan veirifikasi akun anda\n"
                "Tekan tombol kontak di bawah ini untuk memverifikasi akun anda.",
                reply_markup=markup.as_markup(resize_keyboard=True, one_time_keyboard=True)  # You can add a contact request button here if needed
            )
            return  # Block the handler from executing
        
        contact_data = {
            "contact_verified": True,
            "contact_phone": contact.phone_number,
            "contact_name": contact.first_name,
            "user_id": event.from_user.id
        }

        telegram_data_model = ModelTelegramData(state=self.fsm_context, **contact_data)
        await telegram_data_model.save_to_state()

        data['telegram_data'] = telegram_data_model

        event.delete()
        return await handler(event, data)