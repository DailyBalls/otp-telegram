"""
Usage examples for OTP API with authentication decorator
"""

from .api_client import OTPAPIClient
from .exceptions import InvalidSessionError

async def example_usage():
    """Example of how to use the authenticated API client with lazy cookie loading"""
    
    # Initialize client (you'll need to pass your actual parameters)
    # client = OTPAPIClient(state=fsm_context, user_id=12345, base_url="https://your-api.com")
    
    # Cookies are automatically loaded from state when needed
    # You can check if cookies are loaded: client.is_cookies_loaded()
    
    try:
        # This will automatically load cookies from state and check for JSESSIONID and PLAY_SESSION cookies
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
    """Example of checking authentication before making requests with lazy loading"""
    
    # client = OTPAPIClient(state=fsm_context, user_id=12345, base_url="https://your-api.com")
    
    # Check if user is authenticated (automatically loads cookies from state)
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

async def force_reload_cookies_example():
    """Example of forcing cookie reload when state might have changed"""
    
    # client = OTPAPIClient(state=fsm_context, user_id=12345, base_url="https://your-api.com")
    
    # Force reload cookies from state (useful after state updates)
    await client.force_reload_cookies()
    
    # Now check authentication with fresh cookies
    is_authenticated = await client.check_authentication()
    print(f"Authentication status after reload: {is_authenticated}")
