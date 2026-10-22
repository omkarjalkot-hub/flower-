"""Product queries (no Streamlit dependency)."""
from db import query, query_one

_IMG = ("(SELECT image_path FROM product_images WHERE product_id = p.id "
        "ORDER BY is_primary DESC, id LIMIT 1)")

SORT_OPTIONS = {
    "Newest": "p.id DESC",
    "Price: low to high": "p.price ASC, p.id",
    "Price: high to low": "p.price DESC, p.id",
}


def categories():
    return query("SELECT * FROM categories ORDER BY name")


def categories_in_use():
    """Only categories that have at least one visible listing, biggest first."""
    return query("""SELECT c.*, (SELECT COUNT(*) FROM products p WHERE p.category_id = c.id AND p.is_active = 1) AS n
                    FROM categories c WHERE n > 0 ORDER BY n DESC, c.name""")


def price_bounds():
    row = query_one("SELECT MIN(price) AS lo, MAX(price) AS hi FROM products WHERE is_active = 1")
    if not row or row["lo"] is None:
        return 0, 0
    return int(row["lo"]), int(-(-row["hi"] // 1))


def list_products(search="", category_id=None, price_min=None, price_max=None,
                  sort="Newest", in_stock_only=False):
    sql = (f"SELECT p.*, c.name AS category_name, {_IMG} AS image_path "
           "FROM products p LEFT JOIN categories c ON c.id = p.category_id "
           "WHERE p.is_active = 1")
    params = []
    term = (search or "").strip()
    if term:
        like = f"%{term}%"
        sql += " AND (p.name LIKE ? OR p.description LIKE ?)"
        params += [like, like]
    if category_id:
        sql += " AND p.category_id = ?"
        params.append(category_id)
    if price_min is not None:
        sql += " AND p.price >= ?"
        params.append(price_min)
    if price_max is not None:
        sql += " AND p.price <= ?"
        params.append(price_max)
    if in_stock_only:
        sql += " AND p.stock > 0"
    sql += " ORDER BY " + SORT_OPTIONS.get(sort, SORT_OPTIONS["Newest"])
    return query(sql, params)


def get_product(product_id):
    return query_one(
        f"SELECT p.*, c.name AS category_name, {_IMG} AS image_path "
        "FROM products p LEFT JOIN categories c ON c.id = p.category_id "
        "WHERE p.id = ? AND p.is_active = 1", (product_id,))


def product_images(product_id):
    return query("SELECT * FROM product_images WHERE product_id = ? "
                 "ORDER BY is_primary DESC, id", (product_id,))


def related_products(product, limit=3):
    return query(
        f"SELECT p.*, {_IMG} AS image_path FROM products p "
        "WHERE p.is_active = 1 AND p.category_id = ? AND p.id != ? ORDER BY p.is_featured DESC, p.id LIMIT ?",
        (product["category_id"], product["id"], limit))
