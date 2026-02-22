"""
Utility functions for data parsing and transformation.
"""

import re
from typing import Optional


def parse_fee(raw_fee: str) -> Optional[int]:
    """
    Convert Transfermarkt fee string to integer euros.
    
    Examples:
        "€25.00m" -> 25000000
        "€800Th." -> 800000
        "Free transfer" -> None
        "?" -> None
    
    Args:
        raw_fee: Raw fee string from Transfermarkt
        
    Returns:
        Fee amount in euros as integer, or None if undisclosed/free
    """
    # These strings appear on Transfermarkt for undisclosed or no-fee moves
    if not raw_fee or raw_fee.strip() in ["?", "-", "Free transfer", "Loan"]:
        return None

    cleaned = raw_fee.replace("€", "").replace("£", "").replace("$", "").strip()

    # Transfermarkt formats fees as "25.00m" (millions) or "800Th." (thousands)
    match = re.search(r"([\d.]+)\s*(m|bn|k|th\.?)", cleaned, re.IGNORECASE)

    if not match:
        return None

    value = float(match.group(1))
    unit = match.group(2).lower()

    # Convert the matched unit to a full integer euro amount
    if unit in ["m", "mn"]:
        return int(value * 1_000_000)
    elif unit == "bn":
        return int(value * 1_000_000_000)
    elif unit in ["k", "th", "th."]:
        return int(value * 1_000)

    return None


def extract_player_id(url: str) -> Optional[str]:
    """
    Extract player ID from Transfermarkt URL.
    
    Example:
        "/spieler/123456/cristiano-ronaldo" -> "123456"
        "https://www.transfermarkt.com/spieler/123456" -> "123456"
    
    Args:
        url: Player profile URL or path
        
    Returns:
        Player ID string, or None if not found
    """
    # Player IDs appear after "/spieler/" in all Transfermarkt player URLs
    match = re.search(r"/spieler/(\d+)", url)
    return match.group(1) if match else None
