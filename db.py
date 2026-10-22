"""SQLite access layer: connection helpers, schema, and first-run seed data."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from utils.images import make_qr_placeholder

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "flower_shop.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'customer' CHECK (role IN ('customer', 'admin')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS addresses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    label TEXT,
    recipient_name TEXT NOT NULL,
    phone TEXT NOT NULL,
    house_flat TEXT NOT NULL,
    street TEXT NOT NULL,
    area_landmark TEXT NOT NULL,
    city TEXT NOT NULL,
    state TEXT NOT NULL,
    pin_code TEXT NOT NULL,
    is_default INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    image_path TEXT
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    name TEXT NOT NULL,
    description TEXT,
    price REAL NOT NULL CHECK (price >= 0),
    stock INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
    is_bundle INTEGER NOT NULL DEFAULT 0,
    is_featured INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS product_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    image_path TEXT NOT NULL,
    is_primary INTEGER NOT NULL DEFAULT 0,
    is_placeholder INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS cart_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    UNIQUE (user_id, product_id)
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    order_number TEXT NOT NULL UNIQUE,
    subtotal REAL NOT NULL,
    delivery_fee REAL NOT NULL DEFAULT 0,
    total REAL NOT NULL,
    order_status TEXT NOT NULL DEFAULT 'Pending verification',
    payment_status TEXT NOT NULL DEFAULT 'Pending verification',
    delivery_note TEXT,
    ship_name TEXT NOT NULL,
    ship_phone TEXT NOT NULL,
    ship_house_flat TEXT NOT NULL,
    ship_street TEXT NOT NULL,
    ship_area TEXT NOT NULL,
    ship_city TEXT NOT NULL,
    ship_state TEXT NOT NULL,
    ship_pin TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    cancelled_at TEXT
);

CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id) ON DELETE SET NULL,
    product_name TEXT NOT NULL,
    unit_price REAL NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0)
);

CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    amount REAL NOT NULL,
    transaction_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Pending verification'
        CHECK (status IN ('Pending verification', 'Approved', 'Rejected')),
    admin_note TEXT,
    submitted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TEXT,
    refunded_at TEXT
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS contact_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

DEFAULT_SETTINGS = {
    "shop_name": "Petal & Bloom",
    "tagline": "Fresh flowers, delivered to the people you love.",
    "qr_image_path": "",
    "delivery_fee": "0",
    "contact_phone": "",
    "contact_email": "",
    "contact_address": "",
    "opening_hours": "",
}

SEED_FLAG = "seed_catalog_v4"
PURGE_FLAG = "purge_placeholder_products_v1"
PHOTO_DIR = "assets/photos"

# (name, description)
SEED_CATEGORIES = [
    ("Roses", "Classic roses for every occasion."),
    ("Mixed Bouquets", "Hand-tied bouquets and gift combos."),
    ("Carnations", "Long-lasting carnations in bold colours."),
    ("Tulips", "Bright spring tulips."),
    ("Marigolds", "Festive marigolds."),
    ("Seasonal Blooms", "Seasonal cut flowers."),
    ("Handmade & Dried", "Crochet and dried flowers that never wilt."),
]

# Every listing has a real photo in assets/photos/ named after it (see assets/photos/FILENAMES.txt).
# (category, name, description, price INR, stock, is_bundle, is_featured)
SEED_PRODUCTS = [
    ("Roses", "Red Rose Bunch (10 stems)", "Ten long-stem red roses, freshly cut and wrapped.", 349, 40, 1, 0),
    ("Roses", "Royal Red Rose Bouquet (24 stems)", "Two dozen deep red roses hand-tied with leaf fillers and a satin ribbon.", 1199, 14, 1, 0),
    ("Roses", "Pink Rose Hand-tied Bouquet", "Fifteen blush pink roses with baby's breath, wrapped by hand.", 749, 16, 1, 0),
    ("Roses", "Hot Pink Rose Bunch (8 stems)", "Eight deep pink roses with long stems, tied and wrapped.", 449, 30, 1, 0),
    ("Roses", "Heart of Roses Bouquet", "Deep red roses around a heart of pink roses, finished with baby's breath and a satin ribbon.", 3499, 5, 1, 0),
    ("Roses", "Red Rose Bouquet in Black Wrap", "Two dozen red roses with baby's breath in black tissue wrap and a red bow.", 1099, 12, 1, 0),
    ("Roses", "Red Rose & Gypsophila Bouquet", "Red roses with baby's breath in bright red wrapping and a bow.", 799, 20, 1, 0),
    ("Roses", "Pink Roses in Ceramic Vase", "Pink roses with soft greenery, arranged in a white ceramic vase.", 1499, 8, 1, 0),
    ("Roses", "Red Rose & Eucalyptus Bouquet", "Bold red roses with fresh eucalyptus sprigs.", 999, 15, 1, 0),
    ("Roses", "Single Red Rose Bouquet", "One red rose with baby's breath in red wrapping.", 199, 40, 0, 0),
    ("Roses", "Pink Rose Bouquet in Gift Wrap", "Pink roses and baby's breath in printed pink gift wrap.", 849, 16, 1, 0),
    ("Mixed Bouquets", "Sunshine Mixed Bouquet", "Sunflowers, roses and lilies in one sunny vase arrangement.", 899, 12, 1, 0),
    ("Mixed Bouquets", "Celebration Combo", "A mixed rose bouquet in soft wrapping, ready to gift.", 1199, 10, 1, 0),
    ("Mixed Bouquets", "Pastel Dream Bouquet", "Soft pink and lilac blooms in a calm pastel vase arrangement.", 999, 9, 1, 0),
    ("Mixed Bouquets", "Birthday Joy Bouquet", "A colourful birthday bouquet with gerberas, carnations and roses.", 849, 15, 1, 0),
    ("Mixed Bouquets", "White Chrysanthemum & Rose Bouquet", "White chrysanthemums with soft pink roses and greenery.", 649, 16, 1, 0),
    ("Mixed Bouquets", "Pink Rose & Carnation Bouquet", "Pink roses and carnations with eucalyptus in cream wrapping.", 899, 14, 1, 0),
    ("Mixed Bouquets", "Luxe Mixed Flower Bouquet", "Hydrangeas, lilies, carnations and roses in a rich, colourful hand bouquet.", 2199, 6, 1, 0),
    ("Mixed Bouquets", "Purple Lisianthus & Statice Bouquet", "Purple lisianthus, statice and asters with ferns, wrapped in burlap.", 1099, 10, 1, 0),
    ("Mixed Bouquets", "Yellow Rose & Chrysanthemum Bouquet", "Yellow roses, carnations and chrysanthemums with berries and fern.", 1299, 9, 1, 0),
    ("Carnations", "Pink Carnation Bouquet", "Pink carnations with roses and soft fillers, wrapped in pink paper.", 549, 18, 1, 0),
    ("Tulips", "Mixed Tulip Bunch", "A bright mix of tulips in warm spring colours.", 649, 15, 1, 0),
    ("Marigolds", "Marigold Flower Bunch", "Fresh yellow marigolds for puja, decoration or rangoli.", 99, 80, 0, 0),
    ("Seasonal Blooms", "Pink Dahlia Stems (3 stems)", "Three large coral-pink dahlias, a showy seasonal bloom.", 549, 12, 0, 0),
    ("Seasonal Blooms", "Blue Balloon Flower Stems (5 stems)", "Five stems of star-shaped blue-violet balloon flowers.", 399, 15, 0, 0),
    ("Handmade & Dried", "Crochet Rose Bouquet (Red & White)", "Handmade crochet roses in red and white yarn. They never wilt, so it keeps as a lasting gift.", 699, 12, 1, 0),
    ("Handmade & Dried", "Crochet Flower Bouquet (Sunflower, Daisy & Tulip)", "Handmade crochet gerberas, sunflower, daisies and tulips in burlap wrap. Never wilts.", 799, 10, 1, 0),
    ("Handmade & Dried", "Dried Flower Bouquet (Wheat & Lavender)", "Dried wheat, lavender and preserved blooms in kraft paper with a lilac ribbon. Lasts for months.", 699, 12, 1, 0),
]


@contextmanager
def get_conn():
    """Yield a SQLite connection with foreign keys on; commits or rolls back."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def query(sql, params=()):
    """Run a SELECT and return a list of dicts."""
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def query_one(sql, params=()):
    rows = query(sql, params)
    return rows[0] if rows else None


def execute(sql, params=()):
    """Run a single write statement and return the new row id."""
    with get_conn() as conn:
        return conn.execute(sql, params).lastrowid


def get_setting(key, default=""):
    row = query_one("SELECT value FROM settings WHERE key = ?", (key,))
    return row["value"] if row and row["value"] is not None else default


def set_setting(key, value):
    execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )

def _slug(text):
    """File-name friendly name, e.g. 'Red Rose Bunch (10 stems)' -> 'red-rose-bunch-10-stems'."""
    out = "".join(c.lower() if c.isalnum() else "-" for c in text)
    while "--" in out:
        out = out.replace("--", "-")
    return out.strip("-")


def _photo_for(slug):
    """Relative path of a real photo for this product slug, or None."""
    for ext in ("jpg", "jpeg", "png", "webp"):
        if (BASE_DIR / PHOTO_DIR / f"{slug}.{ext}").exists():
            return f"{PHOTO_DIR}/{slug}.{ext}"
    return None


def _purge_placeholder_products(conn):
    """One time: remove listings that only ever had a drawn placeholder (no real photo)."""
    if conn.execute("SELECT 1 FROM settings WHERE key = ?", (PURGE_FLAG,)).fetchone():
        return
    rows = conn.execute(
        """SELECT DISTINCT product_id FROM product_images WHERE is_placeholder = 1
           AND product_id NOT IN (SELECT product_id FROM product_images WHERE is_placeholder = 0)""").fetchall()
    for r in rows:
        files = [x["image_path"] for x in conn.execute(
            "SELECT image_path FROM product_images WHERE product_id = ?", (r["product_id"],))]
        conn.execute("DELETE FROM products WHERE id = ?", (r["product_id"],))
        for rel in files:
            if rel.startswith("assets/products/") and "/uploads/" not in rel:
                try:
                    (BASE_DIR / rel).unlink()
                except OSError:
                    pass
    conn.execute("INSERT INTO settings (key, value) VALUES (?, '1')", (PURGE_FLAG,))


def _seed_catalog(conn):
    """Add any listing that is missing (matched by name), once. Each uses its real photo."""
    if conn.execute("SELECT 1 FROM settings WHERE key = ?", (SEED_FLAG,)).fetchone():
        return
    for name, desc in SEED_CATEGORIES:
        conn.execute("INSERT OR IGNORE INTO categories (name, description) VALUES (?, ?)", (name, desc))
    cat_ids = {r["name"]: r["id"] for r in conn.execute("SELECT id, name FROM categories")}
    for cat, name, desc, price, stock, bundle, featured in SEED_PRODUCTS:
        if conn.execute("SELECT 1 FROM products WHERE name = ?", (name,)).fetchone():
            continue
        photo = _photo_for(_slug(name))
        if not photo:
            continue  # never create a listing without a real photo
        pid = conn.execute(
            "INSERT INTO products (category_id, name, description, price, stock, is_bundle, is_featured) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)", (cat_ids[cat], name, desc, price, stock, bundle, featured)).lastrowid
        conn.execute("INSERT INTO product_images (product_id, image_path, is_primary, is_placeholder) "
                     "VALUES (?, ?, 1, 0)", (pid, photo))
    conn.execute("INSERT INTO settings (key, value) VALUES (?, '1')", (SEED_FLAG,))


def _attach_local_photos(conn):
    """Use real photos dropped into assets/photos/. A file named after the product
    (see assets/photos/FILENAMES.txt) becomes that product's main image."""
    folder = BASE_DIR / PHOTO_DIR
    folder.mkdir(parents=True, exist_ok=True)
    products = conn.execute("SELECT id, name FROM products ORDER BY id").fetchall()
    lines = ["Drop a real photo for a product into this folder using EXACTLY one of these file names",
             "(.jpg, .jpeg, .png or .webp), then restart the app. Square photos look best.", ""]
    for p in products:
        slug = _slug(p["name"])
        lines.append(f"{slug}.jpg    <- {p['name']}")
        rel = _photo_for(slug)
        if not rel:
            continue
        if conn.execute("SELECT 1 FROM product_images WHERE product_id = ? AND image_path = ?",
                        (p["id"], rel)).fetchone():
            continue
        conn.execute("DELETE FROM product_images WHERE product_id = ? AND is_placeholder = 1", (p["id"],))
        conn.execute("UPDATE product_images SET is_primary = 0 WHERE product_id = ?", (p["id"],))
        conn.execute("INSERT INTO product_images (product_id, image_path, is_primary, is_placeholder) "
                     "VALUES (?, ?, 1, 0)", (p["id"], rel))
    (folder / "FILENAMES.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _ensure_qr_placeholder():
    """Give the payment page something to show until the admin uploads the real QR."""
    current = get_setting("qr_image_path", "")
    if current and (BASE_DIR / current).exists():
        return
    set_setting("qr_image_path", make_qr_placeholder("assets/qr/placeholder-qr.png"))


def _write_placeholder_log():
    """List placeholder images still in use, so you know what to replace."""
    rows = query("SELECT pi.image_path, p.name FROM product_images pi JOIN products p ON p.id = pi.product_id "
                 "WHERE pi.is_primary = 1 AND pi.is_placeholder = 1 ORDER BY p.id")
    lines = ["Placeholder images still in use. Replace them with real photos.", ""]
    lines += [f"{r['image_path']}    (Product: {r['name']})" for r in rows]
    qr = get_setting("qr_image_path", "")
    if "placeholder" in qr:
        lines += ["", f"{qr}    (Payment QR: upload your real QR in Admin > Payment QR)"]
    (BASE_DIR / "assets" / "PLACEHOLDERS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def init_db():
    """Create tables on first run, upgrade older databases, seed the photo-backed catalogue once."""
    with get_conn() as conn:
        conn.executescript(SCHEMA)
        pay_cols = [r["name"] for r in conn.execute("PRAGMA table_info(payments)")]
        if "refunded_at" not in pay_cols:
            conn.execute("ALTER TABLE payments ADD COLUMN refunded_at TEXT")
        for k, v in DEFAULT_SETTINGS.items():
            conn.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))
        _attach_local_photos(conn)          # first, so real photos are never mistaken for placeholders
        _purge_placeholder_products(conn)
        _seed_catalog(conn)
        _attach_local_photos(conn)
    _ensure_qr_placeholder()
    _write_placeholder_log()
