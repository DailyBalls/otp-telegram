from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import KeyboardButton, Message
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from config import BotConfig


class VerifyContactMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        pass

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        # Check if FSM context is available
        fsm_context: FSMContext = data['state']
        
        if fsm_context is None:
            # FSM context not available, allow request to continue
            # This can happen if middleware is applied to routers without FSM
            return await handler(event, data)
        
        # Get current FSM data
        fsm_data = await fsm_context.get_data()
        
        # Check if user has already verified their contact
        contact_verified = fsm_data.get("contact_verified", False)
        
        if contact_verified:
            # User has already verified contact, allow request to continue
            return await handler(event, data)
        
        # User hasn't verified contact yet
        # Check if the current message is a contact
        if event.contact:
            # This is a contact message, save the contact data and mark as verified
            contact_data = {
                "contact_verified": True,
                "contact_phone": event.contact.phone_number,
                "contact_name": event.contact.first_name,
                "contact_user_id": event.from_user.id
            }
            
            # Save contact data to FSM storage
            await fsm_context.update_data(**contact_data)
            
            # Allow the contact handler to process this message
            return await handler(event, data)
        
        # User hasn't verified contact and this is not a contact message
        # Block the request and ask for contact

        markup = ReplyKeyboardBuilder()
        b5 = KeyboardButton(text="Share a number", request_contact=True)
        markup.add(b5)
        await event.answer(
            "🔐 <b>Contact Verification Required</b>\n\n"
            "To continue using this bot, please share your contact information.\n"
            "Tap the contact button below to verify your identity.",
            reply_markup=markup.as_markup(resize_keyboard=True, one_time_keyboard=True)  # You can add a contact request button here if needed
        )
        return  # Block the handler from executing
        