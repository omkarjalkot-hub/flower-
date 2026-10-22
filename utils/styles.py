"""Theme: ivory page, white cards, marigold + saffron accents, deep brown text.
Fills the screen, no sidebar, no toolbar, no hover pop-ups on images."""
import streamlit as st

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=Nunito+Sans:wght@400;600;700&display=swap');

:root {
  --marigold: #F5B82E; --saffron: #E8751A; --saffron-dark: #C25A0A;
  --ivory: #FFFDF7; --cream: #FFF4DE; --bark: #2B2118; --muted: #7B6B58; --line: #EADFC8;
}

.stApp, .stMarkdown, p, label, li, input, textarea, select, th, td {
  font-family: 'Nunito Sans', 'Segoe UI', sans-serif;
}
[data-testid="stIconMaterial"], .material-symbols-rounded, .material-icons {
  font-family: 'Material Symbols Rounded' !important;
}
h1, h2, h3, h4 { font-family: 'Fraunces', Georgia, serif !important; color: var(--bark); letter-spacing: -0.01em; }

/* Thin marigold-to-saffron stripe across the very top */
.stApp::before { content: ""; position: fixed; top: 0; left: 0; right: 0; height: 5px; z-index: 1000;
                 background: linear-gradient(90deg, var(--marigold), var(--saffron)); }

/* No sidebar, toolbar, menu */
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"], [data-testid="stSidebarNav"] { display: none !important; }
header[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"],
#MainMenu, footer { display: none !important; }

/* No fullscreen button / hover text on images */
[data-testid="StyledFullScreenButton"], button[title="View fullscreen"], [data-testid="stImage"] button { display: none !important; }

/* Use the whole screen */
.block-container { max-width: 1700px; padding: 1.4rem 3rem 3rem 3rem; }

/* Top bar: big shop name on the left, tight row of links on the right */
.st-key-topbar { border-bottom: 1px solid var(--line); padding-bottom: .9rem; margin-bottom: 1.4rem; }
.st-key-brand a { text-decoration: none; padding: 0; background: transparent !important; }
.st-key-brand a p { font-family: 'Fraunces', Georgia, serif !important; font-size: 2.7rem; font-weight: 700;
                    line-height: 1.05; color: var(--bark); letter-spacing: -0.02em; white-space: nowrap; }
.st-key-navlinks, .st-key-footlinks { display: flex !important; flex-direction: row !important; flex-wrap: nowrap;
                    align-items: center; justify-content: flex-end; gap: 1.1rem !important; }
.st-key-footlinks { justify-content: flex-start; gap: 1.6rem !important; }
.st-key-navlinks > div, .st-key-footlinks > div { width: auto !important; flex: 0 0 auto !important; }
.st-key-topbar [data-testid="stPageLink"] a, .st-key-footlinks [data-testid="stPageLink"] a {
    padding: .3rem .2rem; background: transparent; width: auto; }
.st-key-topbar [data-testid="stPageLink"] a p, .st-key-footlinks [data-testid="stPageLink"] a p {
    font-weight: 600; font-size: .95rem; color: var(--bark); white-space: nowrap; }
.st-key-topbar [data-testid="stPageLink"] a:hover p, .st-key-footlinks [data-testid="stPageLink"] a:hover p {
    color: var(--saffron-dark); text-decoration: underline; }
.st-key-brand [data-testid="stPageLink"] a:hover p { text-decoration: none; color: var(--bark); }
.st-key-signin a { background: var(--saffron) !important; border-radius: 999px; padding: .35rem 1.1rem !important; }
.st-key-signin a p, .st-key-signin a:hover p { color: #fff !important; text-decoration: none !important; }
.st-key-adminnav [data-testid="stPageLink"] a { padding: .25rem .3rem; }
.st-key-adminnav [data-testid="stPageLink"] a p { font-size: .85rem; }
.st-key-navlinks a[href$="orders"]::before, .st-key-navlinks a[href$="cart"]::before {
    content: ""; display: inline-block; flex: 0 0 auto; width: 28px; height: 28px; margin-right: .45rem;
    background-size: contain; background-repeat: no-repeat; background-position: center; }
{ICON_CSS}

/* White inputs, same look as the Filters button */
div[data-baseweb="input"], div[data-baseweb="base-input"], div[data-baseweb="select"] > div,
[data-testid="stPopover"] button {
    background-color: #fff !important; border: 1.5px solid #E0D3BA !important; border-radius: 12px !important; }
div[data-baseweb="input"] input, div[data-baseweb="base-input"] input, div[data-baseweb="select"] input {
    background-color: transparent !important; }
div[data-baseweb="input"]:focus-within, div[data-baseweb="select"] > div:focus-within {
    border-color: var(--saffron) !important; }
.stTextArea textarea { background-color: #fff !important; border-radius: 12px; }

/* Buttons */
.stButton > button, .stFormSubmitButton > button, .stDownloadButton > button {
  border-radius: 999px; border: 1.5px solid #E0D3BA; font-weight: 700; padding: .35rem 1rem; background: #fff; color: var(--bark);
}
.stButton > button:hover { border-color: var(--saffron); color: var(--saffron-dark); }
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primaryFormSubmit"] {
  background: var(--saffron); color: #fff; border-color: var(--saffron);
}
.stButton > button[kind="primary"]:hover, .stFormSubmitButton > button[kind="primaryFormSubmit"]:hover {
  background: var(--saffron-dark); border-color: var(--saffron-dark); color: #fff;
}

/* Product cards */
[class*="st-key-card_"] { background: #fff; border: 1px solid var(--line); border-radius: 16px;
                          padding: .7rem .7rem 1rem .7rem; transition: box-shadow .2s ease; }
[class*="st-key-card_"]:hover { box-shadow: 0 6px 22px rgba(120, 80, 20, .12); }
.pname { font-weight: 700; font-size: 1.02rem; margin: .5rem 0 .1rem 0; line-height: 1.3; display: -webkit-box;
         -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; min-height: 2.6em; }
.pprice { color: var(--saffron-dark); font-weight: 700; font-size: 1.2rem; }
.badge { display: inline-block; padding: .1rem .6rem; border-radius: 999px; font-size: .78rem; font-weight: 700; margin-left: .4rem; }
.badge-out { background: #F6D5CF; color: #8E2B1B; }
.badge-low { background: #FDEBB8; color: #7A5600; }
.badge-in  { background: #DCEBD2; color: #2F5B1E; }
[data-testid="stImage"] img { border-radius: 12px; }
.count-line { color: var(--muted); margin: .2rem 0 1rem 0; }
</style>
"""


def _icon_css():
    """Embed the custom Cart and Track order icons (assets/icons/*.png) into the page styles."""
    import base64
    from pathlib import Path
    from utils.images import make_nav_icons
    folder = Path(__file__).resolve().parent.parent / "assets" / "icons"
    if not (folder / "cart.png").exists() or not (folder / "track.png").exists():
        make_nav_icons()
    css = ""
    for name, href in (("track", "orders"), ("cart", "cart")):
        data = base64.b64encode((folder / f"{name}.png").read_bytes()).decode()
        css += f'.st-key-navlinks a[href$="{href}"]::before {{ background-image: url(data:image/png;base64,{data}); }}\n'
    return css


def apply_theme():
    st.markdown(CSS.replace("{ICON_CSS}", _icon_css()), unsafe_allow_html=True)


def stock_badge(stock: int) -> str:
    if stock <= 0:
        return '<span class="badge badge-out">Out of stock</span>'
    if stock <= 5:
        return f'<span class="badge badge-low">Only {stock} left</span>'
    return '<span class="badge badge-in">In stock</span>'
