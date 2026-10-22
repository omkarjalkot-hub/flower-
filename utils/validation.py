"""Input validation shared by registration, profile and checkout."""
import re

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PIN_RE = re.compile(r"^[1-9][0-9]{5}$")


def valid_email(email: str) -> bool:
    return bool(_EMAIL_RE.match((email or "").strip()))


def normalize_phone(phone: str):
    """Return a 10-digit Indian mobile number, or None if invalid.

    Accepts spaces, dashes and an optional +91 / 91 / 0 prefix.
    """
    digits = re.sub(r"[\s\-()]", "", phone or "")
    if digits.startswith("+"):
        digits = digits[1:]
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    elif len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]
    return digits if re.fullmatch(r"[6-9][0-9]{9}", digits) else None


def valid_pin(pin: str) -> bool:
    return bool(_PIN_RE.match((pin or "").strip()))


def password_problem(password: str):
    """Return a message describing what is wrong, or None if acceptable."""
    if len(password or "") < 8:
        return "Password must be at least 8 characters."
    if not re.search(r"[A-Za-z]", password) or not re.search(r"[0-9]", password):
        return "Password must include at least one letter and one number."
    return None


ADDRESS_FIELDS = [
    ("recipient_name", "Recipient name"),
    ("phone", "Phone number"),
    ("house_flat", "House / flat no."),
    ("street", "Street"),
    ("area_landmark", "Area / landmark"),
    ("city", "City"),
    ("state", "State"),
    ("pin_code", "PIN code"),
]


def validate_address(addr: dict) -> list:
    """Return a list of error messages (empty list means the address is valid)."""
    errors = []
    for key, label in ADDRESS_FIELDS:
        if not str(addr.get(key, "")).strip():
            errors.append(f"{label} is required.")
    if str(addr.get("phone", "")).strip() and normalize_phone(addr["phone"]) is None:
        errors.append("Enter a valid 10-digit mobile number.")
    if str(addr.get("pin_code", "")).strip() and not valid_pin(addr["pin_code"]):
        errors.append("Enter a valid 6-digit PIN code.")
    return errors


INDIAN_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa", "Gujarat",
    "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh",
    "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
    "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh",
    "Uttarakhand", "West Bengal", "Andaman and Nicobar Islands", "Chandigarh",
    "Dadra and Nagar Haveli and Daman and Diu", "Delhi", "Jammu and Kashmir", "Ladakh",
    "Lakshadweep", "Puducherry",
]

_TXN_RE = re.compile(r"^[A-Za-z0-9_\-/]{6,40}$")


def valid_transaction_id(txn: str) -> bool:
    return bool(_TXN_RE.match((txn or "").strip()))
