"""Account logic with no Streamlit dependency: hashing, registration, authentication."""
import hashlib
import hmac
import sqlite3
import secrets

from db import execute, query_one

_ITERATIONS = 260_000
_ALGO = "pbkdf2_sha256"


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), _ITERATIONS)
    return f"{_ALGO}${_ITERATIONS}${salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, iters, salt, digest = stored.split("$")
        if algo != _ALGO:
            return False
        check = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(iters))
        return hmac.compare_digest(check.hex(), digest)
    except (ValueError, AttributeError):
        return False


# Used so a wrong email takes about as long as a wrong password.
_DUMMY_HASH = hash_password("not-a-real-password-1")


def create_user(name, email, phone, password, role="customer"):
    """Insert a user. Returns (ok, message)."""
    email = email.strip().lower()
    try:
        execute(
            "INSERT INTO users (name, email, phone, password_hash, role) VALUES (?, ?, ?, ?, ?)",
            (name.strip(), email, phone, hash_password(password), role),
        )
    except sqlite3.IntegrityError:
        return False, "An account with this email already exists."
    return True, "Account created."


def authenticate(email, password, role):
    """Return the user dict if credentials match AND the account has the given role."""
    user = query_one("SELECT * FROM users WHERE email = ?", ((email or "").strip().lower(),))
    if user is None:
        verify_password(password or "", _DUMMY_HASH)
        return None
    if not verify_password(password or "", user["password_hash"]) or user["role"] != role:
        return None
    return user


def update_profile(user_id, name, phone):
    execute("UPDATE users SET name = ?, phone = ? WHERE id = ?", (name.strip(), phone, user_id))


def change_password(user_id, current_password, new_password):
    """Returns (ok, message)."""
    user = query_one("SELECT password_hash FROM users WHERE id = ?", (user_id,))
    if not user or not verify_password(current_password or "", user["password_hash"]):
        return False, "Your current password is not correct."
    execute("UPDATE users SET password_hash = ? WHERE id = ?", (hash_password(new_password), user_id))
    return True, "Password changed."
