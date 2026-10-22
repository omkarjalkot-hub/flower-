"""Saved delivery addresses (no Streamlit dependency)."""
from db import get_conn, query, query_one
from utils.validation import normalize_phone, validate_address

FIELDS = ["recipient_name", "phone", "house_flat", "street", "area_landmark",
          "city", "state", "pin_code"]


def _clean(data):
    out = {k: str(data.get(k, "") or "").strip() for k in FIELDS}
    out["phone"] = normalize_phone(out["phone"]) or out["phone"]
    return out


def list_addresses(user_id):
    return query("SELECT * FROM addresses WHERE user_id = ? ORDER BY is_default DESC, id", (user_id,))


def get_address(user_id, address_id):
    return query_one("SELECT * FROM addresses WHERE id = ? AND user_id = ?", (address_id, user_id))


def add_address(user_id, data, label="", make_default=False):
    """Returns (True, new_id) or (False, [error messages])."""
    errors = validate_address(data)
    if errors:
        return False, errors
    a = _clean(data)
    with get_conn() as conn:
        count = conn.execute("SELECT COUNT(*) FROM addresses WHERE user_id = ?", (user_id,)).fetchone()[0]
        default = 1 if (count == 0 or make_default) else 0
        if default:
            conn.execute("UPDATE addresses SET is_default = 0 WHERE user_id = ?", (user_id,))
        cur = conn.execute(
            """INSERT INTO addresses (user_id, label, recipient_name, phone, house_flat, street,
                                      area_landmark, city, state, pin_code, is_default)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, label.strip(), a["recipient_name"], a["phone"], a["house_flat"], a["street"],
             a["area_landmark"], a["city"], a["state"], a["pin_code"], default))
        return True, cur.lastrowid


def update_address(user_id, address_id, data, label=""):
    errors = validate_address(data)
    if errors:
        return False, errors
    a = _clean(data)
    with get_conn() as conn:
        conn.execute(
            """UPDATE addresses SET label = ?, recipient_name = ?, phone = ?, house_flat = ?, street = ?,
                      area_landmark = ?, city = ?, state = ?, pin_code = ?
               WHERE id = ? AND user_id = ?""",
            (label.strip(), a["recipient_name"], a["phone"], a["house_flat"], a["street"],
             a["area_landmark"], a["city"], a["state"], a["pin_code"], address_id, user_id))
    return True, address_id


def set_default(user_id, address_id):
    with get_conn() as conn:
        conn.execute("UPDATE addresses SET is_default = 0 WHERE user_id = ?", (user_id,))
        conn.execute("UPDATE addresses SET is_default = 1 WHERE id = ? AND user_id = ?", (address_id, user_id))


def delete_address(user_id, address_id):
    """Delete a saved address. Past orders keep their own copy, so they are not affected."""
    with get_conn() as conn:
        row = conn.execute("SELECT is_default FROM addresses WHERE id = ? AND user_id = ?",
                           (address_id, user_id)).fetchone()
        if not row:
            return
        conn.execute("DELETE FROM addresses WHERE id = ? AND user_id = ?", (address_id, user_id))
        if row["is_default"]:
            conn.execute("UPDATE addresses SET is_default = 1 WHERE id = "
                         "(SELECT id FROM addresses WHERE user_id = ? ORDER BY id LIMIT 1)", (user_id,))


def format_address(a):
    """Multi-line text for an address dict with the saved-address field names."""
    return (f"{a['recipient_name']}, {a['phone']}\n"
            f"{a['house_flat']}, {a['street']}\n"
            f"{a['area_landmark']}\n"
            f"{a['city']}, {a['state']} - {a['pin_code']}")
