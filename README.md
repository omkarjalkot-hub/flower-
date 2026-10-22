# Petal & Bloom - flower shop (Streamlit + SQLite)

## Run it locally
1. Install Python 3.10 or newer (python.org). Check with `python --version`.
2. Open a terminal in this folder, then create and activate a virtual environment:
   - Windows:   `python -m venv .venv`  then  `.venv\Scripts\activate`
   - macOS/Linux: `python3 -m venv .venv`  then  `source .venv/bin/activate`
3. Install (or update) dependencies: `pip install -r requirements.txt`
4. Create the first admin (this also creates the database): `python create_admin.py`
5. Start the shop: `streamlit run app.py`  (opens at http://localhost:8501)

The SQLite file `data/flower_shop.db`, the tables, 5 categories, 12 demo flowers and all
placeholder images are created automatically the first time the app (or create_admin.py) runs.

## First things to do as admin (sign in from "Admin sign in" in the sidebar)
- Payment QR: upload your real QR.
- Shop settings: shop name, delivery fee (0 = free), phone, email, address, opening hours.
- Products: edit prices and stock. The prices and stock numbers of the demo listings are examples, so set your own.

Times are shown in Indian Standard Time (stored as UTC).

## Real flower photos
Put photos in `assets/photos/` named exactly as listed in `assets/photos/FILENAMES.txt`
(for example `red-rose-bunch-10-stems.jpg`), then restart the app. You can also upload photos per
product from Admin > Products.
