"""
Custom exceptions for OTP API
"""

class OTPAPIError(Exception):
    """Base OTP API error"""
    pass

class InvalidSessionError(OTPAPIError):
    """Raised when authentication cookies are missing or invalid"""
    pass

class OTPValidationError(OTPAPIError):
    """Raised when OTP validation fails"""
    pass

class OTPTimeoutError(OTPAPIError):
    """Raised when OTP request times out"""
    pass
