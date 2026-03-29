"""
Phone number normalization utility.

Ensures all phone numbers are stored in canonical +91XXXXXXXXXX format
to prevent duplicate accounts from different input formats.
"""

import re


def normalize_phone(phone: str, default_country_code: str = "91") -> str:
    """
    Normalize a phone number to +91XXXXXXXXXX format.

    Handles formats:
    - 9876543210 → +919876543210
    - +919876543210 → +919876543210
    - 919876543210 → +919876543210
    - 09876543210 → +919876543210
    - +91-9876-543-210 → +919876543210
    - +91 98765 43210 → +919876543210
    """
    phone = phone.strip()

    # Extract the + prefix if present
    has_plus = phone.startswith("+")

    # Strip all non-digit characters
    digits = re.sub(r"[^0-9]", "", phone)

    # Reconstruct based on what we have
    if has_plus and digits.startswith(default_country_code):
        # Already has +91... format
        return f"+{digits}"
    elif digits.startswith(default_country_code) and len(digits) > 10:
        # Has 91... without +
        return f"+{digits}"
    elif digits.startswith("0"):
        # Leading 0 (trunk prefix) — replace with +91
        return f"+{default_country_code}{digits[1:]}"
    else:
        # Raw 10-digit number
        return f"+{default_country_code}{digits}"
