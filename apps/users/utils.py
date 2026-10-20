import re

# نرمال‌سازی به قالب یکتا: 09XXXXXXXXX
_DIGITS = re.compile(r"\D")


def normalize_phone(raw: str) -> str:
    """
    قالب‌های رایج ایرانی را به 09XXXXXXXXX تبدیل می‌کند.
    ورودی‌های نامعتبر ValueError می‌دهند.
    """
    if not raw:
        raise ValueError("شماره تلفن خالی است.")
    digits = _DIGITS.sub("", raw)
    if digits.startswith("0098"):
        digits = digits[4:]
    elif digits.startswith("98") and len(digits) == 12:
        digits = digits[2:]
    if digits.startswith("0") and len(digits) == 11:
        digits = digits[1:]
    if len(digits) != 10 or not digits.startswith("9"):
        raise ValueError("شماره موبایل معتبر نیست.")
    return "0" + digits


def is_valid_phone(raw: str) -> bool:
    try:
        normalize_phone(raw)
        return True
    except ValueError:
        return False