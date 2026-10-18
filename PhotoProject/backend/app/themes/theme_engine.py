from PIL import Image, ImageDraw, ImageFont
import os

PRODUCT_SIZES = {
    "mug_11oz":     (1000, 460),
    "mug_15oz":     (1200, 500),
    "frame_4x6":    (1200, 1800),
    "frame_5x7":    (1500, 2100),
    "frame_6x8":    (1800, 2400),
    "frame_8x10":   (2400, 3000),
    "card_4x4":     (1200, 1200),
    "keychain":     (600, 600),
}

THEME_COLORS = {
    "wedding":    {"bg": "#FFF8F0", "accent": "#D4AF37", "text": "#4A3728"},
    "birthday":   {"bg": "#FFF0F5", "accent": "#FF69B4", "text": "#333333"},
    "nature":     {"bg": "#F0FFF0", "accent": "#228B22", "text": "#1a3a1a"},
    "graduation": {"bg": "#F0F4FF", "accent": "#1C3A8A", "text": "#0a0a2a"},
    "custom":     {"bg": "#FFFFFF", "accent": "#555555", "text": "#111111"},
}

def hex_to_rgb(hex_color: str) -> tuple:
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def apply_theme(
    photo: Image.Image,
    product: str,
    theme: str,
    custom_bg_color: str = None,
    custom_accent: str = None,
    title_text: str = "",
) -> Image.Image:
    if product not in PRODUCT_SIZES:
        raise ValueError(f"Unknown product: {product}")

    w, h = PRODUCT_SIZES[product]
    colors = THEME_COLORS.get(theme, THEME_COLORS["custom"]).copy()

    if custom_bg_color:
        colors["bg"] = custom_bg_color
    if custom_accent:
        colors["accent"] = custom_accent

    canvas = Image.new("RGB", (w, h), hex_to_rgb(colors["bg"]))
    draw = ImageDraw.Draw(canvas)

    # Accent border
    accent_rgb = hex_to_rgb(colors["accent"])
    border = 20
    draw.rectangle([border, border, w - border, h - border],
                   outline=accent_rgb, width=6)

    # Place photo — fit inside canvas with padding
    pad = 60
    photo_rgba = photo.convert("RGBA")
    max_w = w - pad * 2
    max_h = h - pad * 2 - (80 if title_text else 0)
    photo_rgba.thumbnail((max_w, max_h), Image.LANCZOS)

    px = (w - photo_rgba.width) // 2
    py = pad
    canvas.paste(photo_rgba, (px, py), photo_rgba)

    # Title text
    if title_text:
        try:
            font = ImageFont.truetype("arial.ttf", size=48)
        except Exception:
            font = ImageFont.load_default()
        text_rgb = hex_to_rgb(colors["text"])
        bbox = draw.textbbox((0, 0), title_text, font=font)
        tw = bbox[2] - bbox[0]
        tx = (w - tw) // 2
        ty = h - 70
        draw.text((tx, ty), title_text, fill=text_rgb, font=font)

    return canvas
