"""Generates simple flower-themed placeholder images with Pillow.

Every image created here is a PLACEHOLDER. db.py records them in
assets/PLACEHOLDERS.txt so you know exactly which files to replace.
"""
import io
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

BASE_DIR = Path(__file__).resolve().parent.parent

# (background top, background bottom, petal colour)
PALETTES = {
    "Roses": ((253, 226, 218), (246, 170, 150), (200, 50, 60)),
    "Lilies": ((255, 250, 240), (248, 220, 190), (250, 245, 235)),
    "Tulips": ((255, 236, 214), (250, 190, 140), (232, 96, 60)),
    "Marigolds": ((255, 240, 190), (250, 200, 80), (240, 140, 20)),
    "Mixed Bouquets": ((255, 238, 205), (250, 205, 150), (230, 120, 40)),
    "Orchids": ((247, 238, 250), (222, 192, 236), (170, 90, 180)),
    "Sunflowers & Gerberas": ((255, 246, 195), (250, 216, 95), (250, 196, 30)),
    "Carnations": ((255, 232, 238), (246, 172, 192), (220, 70, 110)),
}
DEFAULT_PALETTE = ((255, 240, 205), (250, 205, 150), (230, 120, 40))


def _font(size: int):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # very old Pillow
        return ImageFont.load_default()


def make_placeholder(rel_path: str, title: str, palette_key: str, size=(800, 800)) -> str:
    """Create a placeholder PNG at rel_path (relative to the project root)."""
    top, bottom, petal = PALETTES.get(palette_key, DEFAULT_PALETTE)
    w, h = size
    img = Image.new("RGB", size, top)
    draw = ImageDraw.Draw(img)
    for y in range(h):
        t = y / (h - 1)
        color = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        draw.line([(0, y), (w, y)], fill=color)

    cx, cy = w // 2, int(h * 0.42)
    pr, dist = int(w * 0.115), int(w * 0.18)  # petal radius, distance from centre
    edge = tuple(max(0, c - 45) for c in petal)
    for k in range(8):
        a = math.radians(k * 45)
        px, py = cx + int(math.cos(a) * dist), cy + int(math.sin(a) * dist)
        draw.ellipse([px - pr, py - pr, px + pr, py + pr], fill=petal, outline=edge, width=3)
    cr = int(w * 0.09)
    draw.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], fill=(245, 184, 46), outline=(200, 140, 20), width=3)

    font = _font(int(w * 0.048))
    label = title if len(title) <= 30 else title[:29] + "…"
    box = draw.textbbox((0, 0), label, font=font)
    draw.text(((w - (box[2] - box[0])) / 2, h * 0.80), label, fill=(58, 38, 22), font=font)

    out = BASE_DIR / rel_path
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG")
    return rel_path


def make_qr_placeholder(rel_path: str, size: int = 600) -> str:
    """A fake, NON-scannable QR-style image so the payment page can be tested.
    The admin replaces it with the real payment QR from the admin dashboard."""
    import random
    rnd = random.Random(7)
    n, margin = 25, 50
    cell = (size - 2 * margin - 40) // n
    img = Image.new("RGB", (size, size), "white")
    d = ImageDraw.Draw(img)
    finder = [(0, 0), (n - 7, 0), (0, n - 7)]
    for gy in range(n):
        for gx in range(n):
            in_finder = any(fx <= gx < fx + 7 and fy <= gy < fy + 7 for fx, fy in finder)
            if in_finder:
                continue
            if rnd.random() < 0.5:
                x, y = margin + gx * cell, margin + gy * cell
                d.rectangle([x, y, x + cell - 1, y + cell - 1], fill=(40, 40, 40))
    for fx, fy in finder:
        x, y = margin + fx * cell, margin + fy * cell
        d.rectangle([x, y, x + 7 * cell - 1, y + 7 * cell - 1], fill=(40, 40, 40))
        d.rectangle([x + cell, y + cell, x + 6 * cell - 1, y + 6 * cell - 1], fill="white")
        d.rectangle([x + 2 * cell, y + 2 * cell, x + 5 * cell - 1, y + 5 * cell - 1], fill=(40, 40, 40))
    font = _font(int(size * 0.04))
    label = "DEMO QR - replace in Admin"
    box = d.textbbox((0, 0), label, font=font)
    d.text(((size - (box[2] - box[0])) / 2, size - 42), label, fill=(200, 80, 20), font=font)
    out = BASE_DIR / rel_path
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG")
    return rel_path


def save_upload(data: bytes, subdir: str, stem: str, fmt: str = "JPEG", max_side: int = 1200) -> str:
    """Validate an uploaded image, re-encode it (this strips anything hidden in the file) and
    save it as assets/<subdir>/<stem>.jpg or .png. Returns the path relative to the project root.
    Raises ValueError with a message that is safe to show."""
    try:
        probe = Image.open(io.BytesIO(data))
        probe.verify()
        img = Image.open(io.BytesIO(data))
    except Exception:
        raise ValueError("That file is not a valid image.")
    if img.format not in ("PNG", "JPEG", "WEBP"):
        raise ValueError("Use a PNG, JPG or WEBP image.")
    img = ImageOps.exif_transpose(img).convert("RGB")
    img.thumbnail((max_side, max_side))
    ext = "png" if fmt == "PNG" else "jpg"
    rel = f"{subdir}/{stem}.{ext}"
    out = BASE_DIR / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, fmt, **({"quality": 88} if fmt == "JPEG" else {}))
    return rel


def make_logo(rel_path: str, size: int = 512) -> str:
    """Shop logo: a white lotus-style bloom on a warm marigold-to-saffron round badge."""
    S = size * 3
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    # badge with diagonal gradient
    grad = Image.new("RGBA", (S, S))
    gd = ImageDraw.Draw(grad)
    c1, c2 = (247, 196, 60), (226, 100, 18)
    for i in range(2 * S):
        t = i / (2 * S - 1)
        col = tuple(int(c1[k] + (c2[k] - c1[k]) * t) for k in range(3)) + (255,)
        gd.line([(i, 0), (0, i)], fill=col, width=2)
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).ellipse([int(S * 0.02), int(S * 0.02), int(S * 0.98), int(S * 0.98)], fill=255)
    img.paste(grad, (0, 0), mask)

    px, py = S * 0.5, S * 0.74           # where all petals meet
    def petal(angle, length, width, fill, edge):
        pts = []
        for i in range(0, 61):
            t = i / 60
            x = (width / 2) * math.sin(math.pi * t ** 0.72)
            pts.append((x, -length * t))
        pts = pts + [(-x, y) for x, y in reversed(pts)]
        a = math.radians(angle)
        rot = [(px + x * math.cos(a) - y * math.sin(a), py + x * math.sin(a) + y * math.cos(a)) for x, y in pts]
        layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        d.polygon(rot, fill=fill)
        d.line(rot + [rot[0]], fill=edge, width=max(4, S // 140), joint="curve")
        return layer

    edge = (190, 84, 10, 255)
    for angle, length, width, fill in [
        (-72, S * 0.34, S * 0.20, (255, 232, 190, 255)),
        (72, S * 0.34, S * 0.20, (255, 232, 190, 255)),
        (-38, S * 0.43, S * 0.22, (255, 244, 224, 255)),
        (38, S * 0.43, S * 0.22, (255, 244, 224, 255)),
        (0, S * 0.50, S * 0.24, (255, 255, 255, 255)),
    ]:
        img = Image.alpha_composite(img, petal(angle, length, width, fill, edge))
    # little water lines under the bloom
    d = ImageDraw.Draw(img)
    for dy, half in ((S * 0.745, S * 0.27), (S * 0.80, S * 0.17)):
        d.arc([S * 0.5 - half, dy - S * 0.03, S * 0.5 + half, dy + S * 0.05], 15, 165,
              fill=(255, 255, 255, 255), width=max(6, S // 90))
    out = BASE_DIR / rel_path
    out.parent.mkdir(parents=True, exist_ok=True)
    img.resize((size, size), Image.LANCZOS).save(out, "PNG")
    return rel_path


def make_nav_icons(folder: str = "assets/icons", size: int = 96):
    """Two custom icons for the header: a flower basket (Cart) and a parcel with a map pin (Track order)."""
    S = size * 4
    k = S / 384

    def new():
        im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        return im, ImageDraw.Draw(im)

    def P(*pts):
        return [(x * k, y * k) for x, y in pts]

    ink, saffron, light, gold, leaf = (178, 80, 8, 255), (232, 117, 26, 255), (243, 154, 59, 255), (245, 184, 46, 255), (79, 138, 60, 255)

    # ---- basket with a flower ----
    cart, d = new()
    d.line(P((192, 176), (192, 112)), fill=leaf, width=int(12 * k))
    d.polygon(P((192, 150), (150, 118), (160, 150)), fill=leaf)
    d.polygon(P((192, 140), (236, 108), (226, 142)), fill=leaf)
    for a in range(0, 360, 60):
        x, y = 192 + 40 * math.cos(math.radians(a)), 78 + 40 * math.sin(math.radians(a))
        d.ellipse([(x - 34) * k, (y - 34) * k, (x + 34) * k, (y + 34) * k], fill=gold, outline=(226, 160, 28, 255), width=int(5 * k))
    d.ellipse([(192 - 24) * k, (78 - 24) * k, (192 + 24) * k, (78 + 24) * k], fill=ink)
    d.polygon(P((60, 212), (324, 212), (292, 346), (92, 346)), fill=light, outline=ink)
    d.line(P((60, 212), (324, 212), (292, 346), (92, 346), (60, 212)), fill=ink, width=int(9 * k), joint="curve")
    for x0, x1 in ((120, 128), (192, 192), (264, 256)):
        d.line(P((x0, 222), (x1, 338)), fill=ink, width=int(8 * k))
    d.line(P((72, 262), (312, 262)), fill=ink, width=int(8 * k))
    d.rounded_rectangle([40 * k, 184 * k, 344 * k, 224 * k], radius=int(16 * k), fill=saffron, outline=ink, width=int(9 * k))

    # ---- parcel with a pin ----
    trk, d = new()
    d.rounded_rectangle([26 * k, 168 * k, 250 * k, 350 * k], radius=int(14 * k), fill=(255, 241, 214, 255), outline=ink, width=int(10 * k))
    d.rectangle([26 * k, 168 * k, 250 * k, 214 * k], fill=gold, outline=ink, width=int(10 * k))
    d.rectangle([114 * k, 168 * k, 162 * k, 350 * k], fill=saffron)
    d.line(P((114, 168), (114, 350)), fill=ink, width=int(7 * k))
    d.line(P((162, 168), (162, 350)), fill=ink, width=int(7 * k))
    d.ellipse([196 * k, 38 * k, 360 * k, 202 * k], fill=saffron, outline=ink, width=int(9 * k))
    d.polygon(P((208, 148), (348, 148), (278, 268)), fill=saffron)
    d.line(P((206, 150), (278, 268), (350, 150)), fill=ink, width=int(9 * k), joint="curve")
    d.ellipse([196 * k, 38 * k, 360 * k, 202 * k], fill=saffron, outline=ink, width=int(9 * k))
    d.ellipse([248 * k, 90 * k, 308 * k, 150 * k], fill=(255, 255, 255, 255), outline=ink, width=int(6 * k))

    out = BASE_DIR / folder
    out.mkdir(parents=True, exist_ok=True)
    cart.resize((size, size), Image.LANCZOS).save(out / "cart.png", "PNG")
    trk.resize((size, size), Image.LANCZOS).save(out / "track.png", "PNG")
