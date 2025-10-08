"""
Simple OTP API Client
"""
import aiohttp
from typing import Dict, Any, Optional
from .models import APIResponse
from .decorators import authenticated
from .exceptions import InvalidSessionError
from aiogram.fsm.context import FSMContext


class OTPAPIClient:
    """Simple OTP API Client with aiohttp"""
    
    def __init__(self, state: FSMContext, user_id: int, base_url: str):
        self.telegram_id = user_id
        self.base_url = base_url
        self.state = state
        self.cookie_jar = None
        self.headers = {
            "X-Telegram-User-Id": str(self.telegram_id),
            "Content-Type": "application/json",
            "User-Agent": "OTP-Telegrum-Bot/1.0"
        }
    
    def add_header(self, key: str, value: str):
        """Add custom header"""
        self.headers[key] = value
    
    def add_headers(self, headers: Dict[str, str]):
        """Add multiple custom headers"""
        self.headers.update(headers)
    
    def remove_header(self, key: str):
        """Remove a header"""
        if key in self.headers:
            del self.headers[key]
    
    async def _load_cookies_from_state(self) -> aiohttp.CookieJar:
        """Load cookies from FSMContext state"""
        try:
            fsm_data = await self.state.get_data()
            cookie_data = fsm_data.get("cookie_jar", {})
            
            if not cookie_data:
                return aiohttp.CookieJar()
            
            cookie_jar = aiohttp.CookieJar()
            for domain, cookies in cookie_data.items():
                for cookie_name, cookie_value in cookies.items():
                    cookie_jar.update_cookies({cookie_name: cookie_value}, domain)
            
            return cookie_jar
        except Exception:
            return aiohttp.CookieJar()
    
    async def _save_cookies_to_state(self, cookie_jar: aiohttp.CookieJar):
        """Save cookies to FSMContext state"""
        try:
            cookie_data = {}
            for cookie in cookie_jar:
                # Handle Morsel objects properly
                domain = getattr(cookie, 'domain', None) or "default"
                if domain not in cookie_data:
                    cookie_data[domain] = {}
                cookie_data[domain][cookie.key] = cookie.value
            
            await self.state.update_data(cookie_jar=cookie_data)
        except Exception as e:
            print(f"Warning: Failed to save cookies: {e}")
    
    async def clear_cookies(self):
        """Clear all cookies and update state"""
        self.cookie_jar.clear()
        await self.state.update_data(cookie_jar={})
    
    def _has_required_cookies(self) -> bool:
        """Check if required authentication cookies are present"""
        if not self.cookie_jar:
            return False
        
        required_cookies = {'JSESSIONID', 'PLAY_SESSION'}
        cookie_names = {cookie.key for cookie in self.cookie_jar}
        
        return required_cookies.issubset(cookie_names)
    
    async def check_authentication(self) -> bool:
        """Check if user is properly authenticated"""
        return self._has_required_cookies()
    
    async def _make_request(self, method: str, endpoint: str, data: Dict[str, Any] = None, custom_headers: Dict[str, str] = None) -> APIResponse:
        """Make HTTP request and return APIResponse"""
        # Merge custom headers with default headers
        headers = self.headers.copy()
        if custom_headers:
            headers.update(custom_headers)
        
        try:
            if self.cookie_jar is None:
                self.cookie_jar = await self._load_cookies_from_state()
            # Use persistent session with cookie jar
            async with aiohttp.ClientSession(cookie_jar=self.cookie_jar) as session:
                async with session.request(
                    method=method,
                    url=f"{self.base_url}{endpoint}",
                    headers=headers,
                    json=data
                ) as response:
                    # Save cookies from response to state
                    await self._save_cookies_to_state(self.cookie_jar)
                    
                    response_data = await response.json()
                    return APIResponse(response_data)
        except Exception as e:
            # Return error response for network issues
            error_response = {
                "error": {
                    "code": 500,
                    "message": f"Network error: {str(e)}"
                },
                "data": None,
                "metadata": {}
            }
            return APIResponse(error_response)
    
    # Auth endpoints
    async def ask_auth(self) -> APIResponse:
        """POST request to /api/v1/telegram/ask-auth"""
        return await self._make_request("POST", "/api/v1/telegram/ask-auth")
    
    async def open_login_form(self) -> APIResponse:
        """GET request to open login form (if needed)"""
        return await self._make_request("GET", "/api/v1/telegram/login-form")

    async def list_active_bank(self) -> APIResponse:
        """GET request to /api/v1/telegram/bank"""
        return await self._make_request("GET", "/api/v1/telegram/bank")

    async def submit_registration(self, data: Dict[str, Any]) -> APIResponse:
        """POST request to /api/v1/telegram/register"""
        print(data)
        return await self._make_request("POST", "/api/v1/telegram/register", data)

    @authenticated
    async def me(self) -> APIResponse:
        """GET request to /api/v1/telegram/me - requires authentication"""
        return await self._make_request("GET", "/api/v1/telegram/me")
