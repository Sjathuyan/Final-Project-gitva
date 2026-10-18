"""PSD template engine — replaces photo placeholder layers with user photos."""
from PIL import Image
import os, io, re

try:
    from psd_tools import PSDImage
    from psd_tools.constants import Tag
    HAS_PSD = True
except ImportError:
    HAS_PSD = False

# Names / patterns that identify photo placeholder layers
PHOTO_LAYER_PATTERNS = [
    r"^person$", r"^image$", r"^birthday person$", r"^birthday girl image$",
    r"^birthday boy image$", r"magnific", r"little-girl", r"little-boy",
    r"caucasian", r"graphic-woman", r"product$",
]

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "Set 1")
THUMB_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "static", "templates")


def _is_photo_layer(name: str) -> bool:
    n = name.lower().strip()
    return any(re.search(p, n) for p in PHOTO_LAYER_PATTERNS)


def list_templates() -> list:
    """Return list of template dicts with id, category, name, thumb_url."""
    results = []
    if not os.path.isdir(TEMPLATES_DIR):
        return results
    for root, dirs, files in os.walk(TEMPLATES_DIR):
        for f in sorted(files):
            if not f.endswith(".psd"):
                continue
            cat = os.path.basename(root)
            psd_path = os.path.join(root, f)
            stem = f[:-4]
            thumb_name = f"{cat}_{stem}.png".replace(" ", "_")
            thumb_path = os.path.join(THUMB_DIR, thumb_name)
            results.append({
                "id": f"{cat}/{f}",
                "category": cat,
                "name": stem,
                "thumb_url": f"/static/templates/{thumb_name}" if os.path.exists(thumb_path) else None,
                "psd_path": psd_path,
            })
    return results


def render_template(psd_path: str, user_photo: Image.Image) -> Image.Image:
    """Replace photo placeholder in PSD with user_photo, return composited PIL image."""
    if not HAS_PSD:
        raise RuntimeError("psd-tools not installed")

    psd = PSDImage.open(psd_path)
    W, H = psd.width, psd.height

    # Find photo layer index and bounding box
    layers = list(psd)
    photo_idx = None
    photo_bbox = None
    for i, layer in enumerate(layers):
        if _is_photo_layer(layer.name):
            photo_idx = i
            photo_bbox = (layer.left, layer.top, layer.right, layer.bottom)
            break

    if photo_idx is None or photo_bbox is None:
        # No placeholder found — just composite normally
        return psd.composite().convert("RGB")

    pl, pt, pr, pb = photo_bbox
    pw, ph = pr - pl, pb - pt

    # Composite everything below photo layer
    base = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for i in range(photo_idx, len(layers)):  # psd layers are reversed (0=top)
        lyr = layers[i]
        try:
            limg = lyr.composite()
            if limg:
                base.paste(limg, (lyr.left, lyr.top), limg.convert("RGBA").split()[3])
        except Exception:
            pass

    # Paste user photo into placeholder slot
    photo = user_photo.convert("RGBA")
    # Scale to fit the slot while preserving aspect ratio
    photo.thumbnail((pw, ph), Image.LANCZOS)
    # Center in slot
    px = pl + (pw - photo.width) // 2
    py = pt + (ph - photo.height) // 2
    base.paste(photo, (px, py), photo.split()[3])

    # Composite layers above photo (foreground decorations)
    for i in range(0, photo_idx):
        lyr = layers[i]
        try:
            limg = lyr.composite()
            if limg:
                lrgba = limg.convert("RGBA")
                base = Image.alpha_composite(
                    base,
                    _layer_to_canvas(lrgba, lyr.left, lyr.top, W, H)
                )
        except Exception:
            pass

    return base.convert("RGB")


def _layer_to_canvas(layer_img, x, y, W, H):
    """Paste layer_img at (x,y) onto a WxH transparent canvas."""
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    canvas.paste(layer_img, (x, y), layer_img.split()[3])
    return canvas


def make_collage(photos: list, layout: str = "grid") -> Image.Image:
    """Combine multiple PIL images into a single collage image."""
    n = len(photos)
    if n == 0:
        return Image.new("RGB", (1200, 900), (30, 30, 50))
    if n == 1:
        return photos[0].convert("RGB")

    if layout == "side":
        # Side by side
        max_h = max(p.height for p in photos)
        resized = []
        for p in photos:
            r = max_h / p.height
            resized.append(p.resize((int(p.width * r), max_h), Image.LANCZOS))
        total_w = sum(r.width for r in resized) + 10 * (n - 1)
        canvas = Image.new("RGB", (total_w, max_h), (20, 20, 35))
        x = 0
        for r in resized:
            canvas.paste(r.convert("RGB"), (x, 0))
            x += r.width + 10
        return canvas
    else:
        # Grid layout
        cols = 2 if n <= 4 else 3
        rows = (n + cols - 1) // cols
        cell_w, cell_h = 1200 // cols, 900 // rows
        canvas = Image.new("RGB", (cell_w * cols, cell_h * rows), (20, 20, 35))
        for i, p in enumerate(photos):
            img = p.convert("RGB").copy()
            img.thumbnail((cell_w - 8, cell_h - 8), Image.LANCZOS)
            ox = (i % cols) * cell_w + (cell_w - img.width) // 2
            oy = (i // cols) * cell_h + (cell_h - img.height) // 2
            canvas.paste(img, (ox, oy))
        return canvas
