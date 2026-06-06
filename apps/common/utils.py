import re


def normalize_phone(value):
    """Normalize an Uzbek phone to '+998XXXXXXXXX' (12 digits after +).

    Strips spaces, dashes, parentheses. Accepts 9-digit local numbers and
    prepends 998. Returns the value unchanged if it can't be normalized.
    """
    if not value:
        return value
    digits = re.sub(r"\D", "", str(value))
    if digits.startswith("00998"):
        digits = digits[2:]
    if len(digits) == 9:           # 901234567 -> 998901234567
        digits = "998" + digits
    if len(digits) == 12 and digits.startswith("998"):
        return "+" + digits
    return value  # leave as-is if unexpected format
