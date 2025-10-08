"""
Authentication decorators for OTP API
"""
import functools
from typing import Callable, Any
from .exceptions import InvalidSessionError

def authenticated(func: Callable) -> Callable:
    """
    Decorator to check for required authentication cookies.
    
    Requires JSESSIONID and PLAY_SESSION cookies to be present.
    Raises InvalidSessionError if cookies are missing.
    """
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        # Check if required cookies exist
        if not self._has_required_cookies():
            raise InvalidSessionError("Missing required authentication cookies (JSESSIONID, PLAY_SESSION)")
        
        return await func(self, *args, **kwargs)
    
    return wrapper
