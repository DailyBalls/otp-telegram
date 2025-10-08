"""
Usage examples for OTP API with authentication decorator
"""

from .api_client import OTPAPIClient
from .exceptions import InvalidSessionError

async def example_usage():
    """Example of how to use the authenticated API client"""
    
    # Initialize client (you'll need to pass your actual parameters)
    # client = OTPAPIClient(state=fsm_context, user_id=12345, base_url="https://your-api.com")
    
    try:
        # This will check for JSESSIONID and PLAY_SESSION cookies
        user_info = await client.me()
        
        if user_info.success:
            print("User info:", user_info.data)
        else:
            print("Error:", user_info.get_error_message())
            
    except InvalidSessionError as e:
        print(f"Authentication required: {e}")
        # Redirect user to login
        # await message.answer("Please login first using /start")
        
    except Exception as e:
        print(f"Unexpected error: {e}")

async def check_authentication_before_action():
    """Example of checking authentication before making requests"""
    
    # client = OTPAPIClient(state=fsm_context, user_id=12345, base_url="https://your-api.com")
    
    # Check if user is authenticated
    is_authenticated = await client.check_authentication()
    
    if not is_authenticated:
        print("User needs to login first")
        return
    
    # Proceed with authenticated actions
    try:
        banks = await client.list_active_bank()
        if banks.success:
            print("Active banks:", banks.data)
    except InvalidSessionError:
        print("Session expired during request")
