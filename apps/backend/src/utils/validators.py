"""
Utility functions for validating and formatting Chilean RUT (Rol Único Tributario).
"""

import re


def validate_rut(rut: str) -> bool:
    """
    Validate Chilean RUT format and check digit.
    
    Args:
        rut: RUT string in format "XXXXXXXX-X" (e.g., "12345678-5" or "12345678-K")
             NO dots allowed.
    
    Returns:
        True if valid, False otherwise
    
    Examples:
        >>> validate_rut("12345678-5")
        True
        >>> validate_rut("11111111-1")
        True
        >>> validate_rut("24876931-K")
        True
        >>> validate_rut("12.345.678-5")  # With dots - REJECTED
        False
    """
    if not rut:
        return False
    
    # Check if format has dots - REJECT
    if "." in rut:
        return False
    
    # Remove hyphen and convert to uppercase
    clean = rut.replace("-", "").upper()
    
    # Must be 8-9 characters (7-8 digits + check digit)
    if not re.match(r'^\d{7,8}[0-9K]$', clean):
        return False
    
    # Split number and check digit
    number = clean[:-1]
    check_digit = clean[-1]
    
    # Calculate expected check digit
    expected = calculate_rut_check_digit(number)
    
    return check_digit == expected



def calculate_rut_check_digit(number: str) -> str:
    """
    Calculate RUT check digit using modulo 11 algorithm.
    
    Args:
        number: RUT number without check digit (e.g., "12345678")
    
    Returns:
        Check digit (0-9 or K)
    
    Examples:
        >>> calculate_rut_check_digit("12345678")
        '5'
        >>> calculate_rut_check_digit("11111111")
        '1'
    """
    reversed_digits = [int(d) for d in reversed(number)]
    factors = [2, 3, 4, 5, 6, 7]
    
    total = sum(digit * factors[i % 6] for i, digit in enumerate(reversed_digits))
    remainder = total % 11
    check = 11 - remainder
    
    if check == 11:
        return '0'
    elif check == 10:
        return 'K'
    else:
        return str(check)


def format_rut(rut: str) -> str:
    """
    Format RUT with dots and hyphen.
    
    Args:
        rut: Unformatted RUT (e.g., "123456785" or "12.345.678-5")
    
    Returns:
        Formatted RUT (e.g., "12.345.678-5")
    
    Examples:
        >>> format_rut("123456785")
        '12.345.678-5'
        >>> format_rut("12345678-5")
        '12.345.678-5'
    """
    # Remove existing formatting
    clean = rut.replace(".", "").replace("-", "").upper()
    
    if len(clean) < 2:
        return rut
    
    # Split number and check digit
    number = clean[:-1]
    check = clean[-1]
    
    # Add thousand separators
    formatted_number = ""
    for i, digit in enumerate(reversed(number)):
        if i > 0 and i % 3 == 0:
            formatted_number = "." + formatted_number
        formatted_number = digit + formatted_number
    
    return f"{formatted_number}-{check}"


def clean_rut(rut: str) -> str:
    """
    Remove formatting from RUT, keeping only digits and K.
    
    Args:
        rut: RUT with or without formatting
    
    Returns:
        Clean RUT without dots or hyphen
    
    Examples:
        >>> clean_rut("12.345.678-5")
        '123456785'
        >>> clean_rut("11.111.111-K")
        '11111111K'
    """
    return rut.replace(".", "").replace("-", "").upper()
