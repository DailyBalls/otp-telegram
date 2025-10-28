"""
Simple OTP API Client
"""
import hashlib
import aiohttp
from typing import Dict, Any, Optional
from .models import APIResponse
from .decorators import authenticated
from .exceptions import InvalidSessionError
from aiogram.fsm.context import FSMContext
from yarl import URL

class OTPAPIClient:
    """Simple OTP API Client with aiohttp"""
    
    def __init__(self, state: FSMContext, user_id: int, base_url: str):
        self.telegram_id = user_id
        self.base_url = base_url
        self.state = state
        self.cookie_jar = aiohttp.CookieJar()  # Initialize empty cookie jar
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
            for cookie_key, cookie_value in cookie_data.items():
                cookie_jar.update_cookies({cookie_key: cookie_value}, URL(self.base_url))
            
            return cookie_jar
        except Exception as e:
            print("Failed to load cookies from state")
            print(e)
            return aiohttp.CookieJar()
    
    async def _save_cookies_to_state(self, cookie_jar: aiohttp.CookieJar):
        """Save cookies to FSMContext state"""
        try:
            cookie_data = {}
            for cookie in cookie_jar:
                cookie_data[cookie.key] = cookie.value
            
            await self.state.update_data(cookie_jar=cookie_data)
        except Exception as e:
            print(f"Warning: Failed to save cookies: {e}")
    
    async def clear_cookies(self):
        """Clear all cookies and update state"""
        self.cookie_jar.clear()
        await self.state.update_data(cookie_jar={})
    
    async def _has_required_cookies(self) -> bool:
        """Check if required authentication cookies are present"""
        if not self.cookie_jar:
            self.cookie_jar = await self._load_cookies_from_state()
        
        required_cookies = {'JSESSIONID', 'PLAY_SESSION'}
        cookie_names = {cookie.key for cookie in self.cookie_jar}
        
        return required_cookies.issubset(cookie_names)
    
    async def check_authentication(self) -> bool:
        """Check if user is properly authenticated"""
        # Ensure cookies are loaded from state
        return await self._has_required_cookies()
    
    async def _make_request(self, method: str, endpoint: str, data: Dict[str, Any] = None, custom_headers: Dict[str, str] = None) -> APIResponse:
        """Make HTTP request and return APIResponse"""
        # Merge custom headers with default headers
        headers = self.headers.copy()
        if custom_headers:
            headers.update(custom_headers)
        if not self.cookie_jar:
            self.cookie_jar = await self._load_cookies_from_state()
        
        try:
            # Use persistent session with cookie jar
            async with aiohttp.ClientSession(cookie_jar=self.cookie_jar) as session:
                async with session.request(
                    method=method,
                    url=f"{self.base_url}{endpoint}",
                    headers=headers,
                    json=data,
                ) as response:
                    # Save cookies from response to state
                    await self._save_cookies_to_state(self.cookie_jar)
                    
                    response_data = await response.json()
                    if response.status == 412:
                        print(f"412 error {response_data.get('error', {}).get('message', 'Unknown error')}, retrying request to {self.base_url}{endpoint}")
                        return await self._make_request(method, endpoint, data, custom_headers)
                    return APIResponse(response_data)
        except Exception as e:
            md5_hash = hashlib.md5(str(e).encode()).hexdigest()
            # Return error response for network issues
            error_response = {
                "error": {
                    "code": 500,
                    "message": f"Mohon hubungi admin\nKode error: <code>{md5_hash}</code>"
                },
                "data": None,
                "metadata": {}
            }
            print("--------------------------------")
            print("Telegram ID: ", self.telegram_id)
            print("URL: ", f"{self.base_url}{endpoint}")
            print("METHOD: ", method)
            print("DATA: ", data)
            print("CUSTOM HEADERS: ", custom_headers)
            print("ERROR HASH: ", md5_hash)
            print("ERROR: ", e)
            return APIResponse(error_response)
    
    async def logout(self) -> APIResponse:
        """POST request to /api/v1/telegram/logout"""
        return await self._make_request("POST", "/api/v1/telegram/logout")
    
    async def submit_login(self, data: Dict[str, Any]) -> APIResponse:
        """POST request to /api/v1/telegram/login"""
        return await self._make_request("POST", "/api/v1/telegram/login", data)

    async def submit_registration(self, data: Dict[str, Any]) -> APIResponse:
        """POST request to /api/v1/telegram/register"""
        return await self._make_request("POST", "/api/v1/telegram/register", data)

    async def ask_auth(self) -> APIResponse:
        """POST request to /api/v1/telegram/ask-auth"""
        return await self._make_request("POST", "/api/v1/telegram/ask-auth")

    async def list_active_bank(self) -> APIResponse:
        """GET request to /api/v1/telegram/bank"""
        return await self._make_request("GET", "/api/v1/telegram/bank")


    @authenticated
    async def me(self) -> APIResponse:
        """GET request to /api/v1/telegram/me - requires authentication"""
        return await self._make_request("POST", "/api/v1/telegram/me")

    @authenticated
    async def list_rekening(self) -> APIResponse:
        """GET request to /api/v1/telegram/me/rekening"""
        return await self._make_request("GET", "/api/v1/telegram/me/rekening")
    
    @authenticated
    async def initiate_rekening_add(self) -> APIResponse:
        """POST request to /api/v1/telegram/rekening/add"""
        return await self._make_request("GET", "/api/v1/telegram/me/rekening/add")

    @authenticated
    async def insert_rekening(self, bank_name: str, bank_account_name: str, bank_account_number: str) -> APIResponse:
        """POST request to /api/v1/telegram/rekening/add"""
        data = {
            "bank_name": bank_name,
            "name": bank_account_name,
            "rekening_bank": bank_account_number
        }
        return await self._make_request("POST", "/api/v1/telegram/me/rekening/add", data)

    @authenticated
    async def search_games(self, search_query: str, page: int = 1) -> APIResponse:
        """POST request to /api/v1/telegram/game/search"""
        data = {
            "search": search_query
        }
        return await self._make_request("POST", f"/api/v1/telegram/game/search?page={page}", data)
        
    @authenticated
    async def get_game_url(self, game_code: str, provider_id: str) -> APIResponse:
        """POST request to /api/v1/telegram/game/launch"""
        data = {
            "game_code": game_code,
            "provider_id": provider_id
        }
        return await self._make_request("POST", f"/api/v1/telegram/game/launch", data)

    @authenticated
    async def list_deposit_payment_channel(self) -> APIResponse:
        """POST request to /api/v1/telegram/deposiy-payment-channel"""
        return await self._make_request("POST", "/api/v1/telegram/bank/deposit-payment-channel")

    @authenticated
    async def initiate_withdraw(self, amount: int) -> APIResponse:
        """POST request to /api/v1/telegram/me/withdraw/initiate"""
        data = {
            "amount": amount
        }
        return await self._make_request("POST", "/api/v1/telegram/me/withdraw/initiate", data)

    @authenticated
    async def confirm_withdraw(self, amount: int, notes: str = "") -> APIResponse:
        """POST request to /api/v1/telegram/me/withdraw/confirm"""
        data = {
            "jumlahwd": amount,
            "catatanwd": notes
        }
        return await self._make_request("POST", "/api/v1/telegram/me/withdraw/confirm", data)

    @authenticated
    async def initiate_deposit(self) -> APIResponse:
        """POST request to /api/v1/telegram/me/deposit/initiate"""
        return await self._make_request("POST", "/api/v1/telegram/me/deposit/initiate")

    @authenticated
    async def confirm_deposit_bank(self, user_bank_id: int, deposit_bank_id: int, amount: int, promo_id: int = None, notes: str = "") -> APIResponse:
        """POST request to /api/v1/telegram/me/deposit/confirm"""
        data = {
            "rekening_user": user_bank_id,
            "rekening_tujuan": deposit_bank_id,
            "jumlah": amount,
            "catatan": notes,
            "promo": str(promo_id) if promo_id is not None else "0",
        }
        return await self._make_request("POST", "/api/v1/telegram/me/deposit/confirm/bank", data)

    async def list_games_by_type(self, game_type = "all", page: int = 1) -> APIResponse:
        """GET request to /api/v1/telegram/game/{game_type}?page={page}"""
        return await self._make_request("GET", f"/api/v1/telegram/game/{game_type}?page={page}")

    async def list_games_by_type_and_provider(self, game_type: str, provider_id: str, page: int = 1) -> APIResponse:
        """GET request to /api/v1/telegram/game/{game_type}/{provider_id}?page={page}"""
        return await self._make_request("GET", f"/api/v1/telegram/game/{game_type}/{provider_id}?page={page}")

    async def list_providers(self, game_type = "all") -> APIResponse:
        """GET request to /api/v1/telegram/provider"""
        return await self._make_request("GET", f"/api/v1/telegram/provider/{game_type}")


    
    
    