"""Banner/product renderer — proper split layout."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np, os

PRODUCTS = {
    "mug_11oz":   {"w": 3300, "h": 1518, "orient": "landscape"},
    "mug_15oz":   {"w": 3900, "h": 1800, "orient": "landscape"},
    "frame_4x6":  {"w": 1800, "h": 1200, "orient": "landscape"},
    "frame_5x7":  {"w": 2100, "h": 1500, "orient": "landscape"},
    "frame_6x8":  {"w": 2400, "h": 1800, "orient": "landscape"},
    "frame_8x10": {"w": 3000, "h": 2400, "orient": "portrait"},
    "card_4x4":   {"w": 1200, "h": 1200, "orient": "square"},
    "keychain":   {"w": 900,  "h": 900,  "orient": "square"},
    "banner_2x3": {"w": 600,  "h": 900,  "orient": "portrait"},
    "banner_3x4": {"w": 900,  "h": 1200, "orient": "portrait"},
}

THEMES = {
    "natural": {
        "bg_top": (20, 70, 20),     "bg_bot": (160, 210, 130),
        "accent": (80, 170, 60),    "text": (255, 255, 255),
        "border": (100, 200, 80),   "text_shadow": (10, 50, 10),
    },
    "wedding": {
        "bg_top": (80, 40, 0),      "bg_bot": (255, 230, 180),
        "accent": (212, 175, 55),   "text": (255, 255, 255),
        "border": (212, 175, 55),   "text_shadow": (60, 20, 0),
    },
    "birthday": {
        "bg_top": (120, 0, 60),     "bg_bot": (255, 160, 80),
        "accent": (255, 220, 50),   "text": (255, 255, 255),
        "border": (255, 200, 50),   "text_shadow": (80, 0, 30),
    },
    "corporate": {
        "bg_top": (10, 20, 60),     "bg_bot": (40, 80, 140),
        "accent": (255, 200, 0),    "text": (255, 255, 255),
        "border": (80, 140, 220),   "text_shadow": (0, 0, 30),
    },
    "elegant": {
        "bg_top": (10, 10, 10),     "bg_bot": (45, 45, 45),
        "accent": (212, 175, 55),   "text": (255, 255, 255),
        "border": (212, 175, 55),   "text_shadow": (0, 0, 0),
    },
}


def _gradient(w, h, top, bot):
    arr = np.zeros((h, w, 3), dtype=np.uint8)
    for i in range(h):
        t = i / h
        arr[i] = [int(top[c] + (bot[c] - top[c]) * t) for c in range(3)]
    return Image.fromarray(arr, "RGB")


def _font(size):
    for name in ["arialbd.ttf", "arial.ttf", "DejaVuSans-Bold.ttf", "DejaVuSans.ttf"]:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _draw_text_with_shadow(draw, pos, text, font, color, shadow):
    x, y = pos
    draw.text((x + 3, y + 3), text, fill=shadow, font=font)
    draw.text((x, y), text, fill=color, font=font)


def _wrap_text(text, font, max_width, draw):
    words = text.split()
    lines, line = [], ""
    for w in words:
        test = (line + " " + w).strip()
        bb = draw.textbbox((0, 0), test, font=font)
        if bb[2] - bb[0] <= max_width:
            line = test
        else:
            if line:
                lines.append(line)
            line = w
    if line:
        lines.append(line)
    return lines


def _hex_to_rgb(h: str) -> tuple:
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def render(
    subject: Image.Image,
    product: str,
    theme: str,
    title: str = "",
    subtitle: str = "",
    subject_scale: float = 0.75,
    subject_x_pct: float = 0.5,
    custom_colors: dict = None,
    decos: dict = None,
) -> Image.Image:
    if product not in PRODUCTS:
        raise ValueError(f"Unknown product: {product}")
    theme = theme if theme in THEMES else "natural"
    decos = decos or {"border": True, "shadow": True, "underline": True, "separator": True}

    p = PRODUCTS[product]
    t = dict(THEMES[theme])  # copy so we can mutate
    if custom_colors:
        for k, v in custom_colors.items():
            if v and k in t:
                t[k] = _hex_to_rgb(v)
    W, H = p["w"], p["h"]
    orient = p["orient"]

    canvas = _gradient(W, H, t["bg_top"], t["bg_bot"]).convert("RGBA")
    draw = ImageDraw.Draw(canvas)

    # Outer border
    bw = max(6, W // 120)
    if decos.get("border", True):
        draw.rectangle([bw, bw, W - bw, H - bw], outline=(*t["border"], 255), width=bw)

    # ---- Determine layout ----
    has_text = bool(title or subtitle)

    if orient == "landscape" and has_text:
        # Photo on left 52%, text on right 48%
        photo_zone = (0, 0, int(W * 0.52), H)
        text_zone_l = int(W * 0.54)
        text_zone_r = W - bw - 30
        text_cx = (text_zone_l + text_zone_r) // 2
        text_start_y = H // 5
    elif orient in ("portrait", "square") and has_text:
        # Photo top 60%, text bottom 40%
        photo_zone = (0, 0, W, int(H * 0.62))
        text_zone_l = bw + 30
        text_zone_r = W - bw - 30
        text_cx = W // 2
        text_start_y = int(H * 0.66)
    else:
        # Full canvas for photo
        photo_zone = (0, 0, W, H)
        text_zone_l = bw + 30
        text_zone_r = W - bw - 30
        text_cx = W // 2
        text_start_y = H // 8

    pz_w = photo_zone[2] - photo_zone[0]
    pz_h = photo_zone[3] - photo_zone[1]

    # ---- Place subject ----
    sub = subject.convert("RGBA")
    max_w = int(pz_w * 0.95)
    max_h = int(pz_h * subject_scale if has_text and orient != "landscape" else pz_h * 0.92)
    sub.thumbnail((max_w, max_h), Image.LANCZOS)

    # Center within photo zone
    px = photo_zone[0] + (pz_w - sub.width) // 2
    py = photo_zone[1] + pz_h - sub.height - max(20, H // 40)

    # Drop shadow
    if decos.get("shadow", True):
        shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sh_img = Image.new("RGBA", sub.size, (0, 0, 0, 100))
        sh_img.putalpha(sub.split()[3])
        shadow.paste(sh_img, (px + 10, py + 10), sh_img)
        shadow = shadow.filter(ImageFilter.GaussianBlur(radius=max(6, W // 200)))
        canvas = Image.alpha_composite(canvas, shadow)
    canvas.paste(sub, (px, py), sub)

    draw = ImageDraw.Draw(canvas)

    # Accent line separator (landscape only, between photo and text)
    if orient == "landscape" and has_text and decos.get("separator", True):
        sep_x = photo_zone[2] + 2
        draw.rectangle([sep_x, H // 8, sep_x + bw, H - H // 8],
                       fill=(*t["accent"], 200))

    # ---- Text ----
    if title:
        max_text_w = text_zone_r - text_zone_l - 40

        # Auto-fit title font — shrink until every line fits inside text zone
        font_size = max(36, H // 5)
        font = _font(font_size)
        lines = _wrap_text(title, font, max_text_w, draw)
        while font_size > 20:
            ok = all(
                draw.textbbox((0, 0), ln, font=font)[2] - draw.textbbox((0, 0), ln, font=font)[0] <= max_text_w
                for ln in lines
            ) and len(lines) <= 3
            if ok:
                break
            font_size = int(font_size * 0.88)
            font = _font(font_size)
            lines = _wrap_text(title, font, max_text_w, draw)

        y = text_start_y
        for line in lines:
            bb = draw.textbbox((0, 0), line, font=font)
            lw = bb[2] - bb[0]
            lh = bb[3] - bb[1]
            x = max(text_zone_l + 10, text_cx - lw // 2)
            _draw_text_with_shadow(draw, (x, y), line, font, t["text"], t["text_shadow"])
            y += lh + max(6, font_size // 6)

        # Accent underline
        acc_y = y + 8
        if decos.get("underline", True):
            ul_len = min(160, max_text_w // 2)
            draw.rectangle([text_cx - ul_len // 2, acc_y,
                            text_cx + ul_len // 2, acc_y + max(4, bw // 2)],
                           fill=(*t["accent"], 230))
        y = acc_y + max(4, bw // 2) + 20

        if subtitle:
            sf = max(20, H // 14)
            sfont = _font(sf)
            slines = _wrap_text(subtitle, sfont, max_text_w, draw)
            while len(slines) > 4 and sf > 16:
                sf = int(sf * 0.88)
                sfont = _font(sf)
                slines = _wrap_text(subtitle, sfont, max_text_w, draw)
            for sline in slines:
                bb = draw.textbbox((0, 0), sline, font=sfont)
                sw = bb[2] - bb[0]
                sh = bb[3] - bb[1]
                x = max(text_zone_l + 10, text_cx - sw // 2)
                _draw_text_with_shadow(draw, (x, y), sline,
                                       sfont, t["accent"], t["text_shadow"])
                y += sh + 8

    return canvas.convert("RGB")


def render_all_products(subject, theme, title, subtitle, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    results = {}
    for key, info in PRODUCTS.items():
        try:
            img = render(subject, key, theme, title, subtitle)
            path = os.path.join(out_dir, f"{key}.png")
            img.save(path, "PNG", dpi=(300, 300))
            results[key] = {"path": path, "label": info.get("label", key), "status": "ok"}
        except Exception as e:
            results[key] = {"path": None, "label": info.get("label", key), "status": str(e)}
    return results
