"""
Simple response models for OTP API
"""
from typing import Dict, List, Any, Optional


class APIResponse:
    """Simple API response model"""
    
    def __init__(self, response_data: dict):
        self.raw = response_data
        self.error = response_data.get('error', {})
        self.data = response_data.get('data')
        self.metadata = response_data.get('metadata', {})
    
    @property
    def success(self) -> bool:
        """Check if the response is successful (HTTP 200)"""
        return self.error.get('code') >= 200 and self.error.get('code') < 300
    
    @property
    def is_error(self) -> bool:
        """Check if the response is an error"""
        return not self.success
    
    @property
    def has_validation_errors(self) -> bool:
        """Check if response has validation errors"""
        return 'validation' in self.metadata
    
    def get_field_errors(self, field_name: str) -> List[str]:
        """Get validation errors for a specific field"""
        return self.metadata.get('validation', {}).get(field_name, [])
    
    def get_first_field_error(self, field_name: str) -> Optional[str]:
        """Get the first validation error for a specific field"""
        errors = self.get_field_errors(field_name)
        return errors[0] if errors else None
    
    def get_error_message(self) -> str:
        """Get the error message"""
        return self.error.get('message', 'Unknown error')
    
    def get_error_code(self) -> int:
        """Get the error code"""
        return self.error.get('code', 0)
    
    @property
    def is_authentication_error(self) -> bool:
        """Check if the response is an authentication error (HTTP Status Code: 401)"""
        return self.error.get('code') == 401
    
    @property
    def is_session_expired(self) -> bool:
        """Check if the session has expired (HTTP Status Code: 401 and session expired message is in the error message)"""
        return self.error.get('code') == 401 and 'session' in self.get_error_message().lower()