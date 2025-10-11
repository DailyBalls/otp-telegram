import re

def alpha_num(value: str) -> bool:
    """
    Checks if the given string is alphanumeric (contains only letters and numbers).

    Args:
        value (str): The string to check.

    Returns:
        bool: True if the string is alphanumeric, False otherwise.
    """
    if not isinstance(value, str):
        return False
    return value.isalnum()


def alpha_space(value: str) -> bool:
    """
    Checks if the given string is alphanumeric (contains only letters and spaces).

    Args:
        value (str): The string to check.

    Returns:
        bool: True if the string is alphanumeric and spaces, False otherwise.
    """
    if not isinstance(value, str):
        return False
    return re.fullmatch(r'^[^\W\d_]+(?: [^\W\d_]+)*$', value, re.UNICODE)

def numeric(value: str) -> bool:
    """
    Checks if the given string is numeric (contains only numbers).

    Args:
        value (str): The string to check.

    Returns:
        bool: True if the string is numeric, False otherwise.
    """
    if not isinstance(value, str):
        return False
    return value.isdigit()

def min_length(value: str|int, min_length: int) -> bool:
    """
    Checks if the given string is at least the minimum length.

    Args:
        value (str|int): The string or int to check.
        min_length (int): The minimum length.

    Returns:
        bool: True if the string is at least the minimum length, False otherwise.
    """
    if not isinstance(value, str|int):
        return False
    return len(str(value)) >= min_length

def max_length(value: str|int, max_length: int) -> bool:
    """
    Checks if the given string is at most the maximum length.

    Args:
        value (str|int): The string or int to check.
        max_length (int): The maximum length.

    Returns:
        bool: True if the string is at most the maximum length, False otherwise.
    """
    if not isinstance(value, str|int):
        return False
    return len(str(value)) <= max_length

def int_min(value: str|int, min_value: int) -> bool:
    """
    Checks if the given integer is at least the minimum value.

    Args:
        value (str|int): The integer to check.
        min_value (int): The minimum value.

    Returns:
        bool: True if the integer is at least the minimum value, False otherwise.
    """
    if not isinstance(value, str|int):
        return False
    if isinstance(value, str) and not numeric(value):
        return False
    return int(value) >= min_value

def int_max(value: str|int, max_value: int) -> bool:
    """
    Checks if the given integer is at most the maximum value.

    Args:
        value (str|int): The integer to check.
        max_value (int): The maximum value.

    Returns:
        bool: True if the integer is at most the maximum value, False otherwise.
    """
    if not isinstance(value, str|int):
        return False
    if isinstance(value, str) and not numeric(value):
        return False
    return int(value) <= max_value