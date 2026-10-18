"""PSD layer inspector and editor — full featured."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io, base64, os, numpy as np

try:
    from psd_tools import PSDImage
    HAS_PSD = True
except ImportError:
    HAS_PSD = False

PHOTO_KINDS = {"pixel", "smartobject"}
TEXT_KIND = "type"
SHAPE_KIND = "shape"
BG_NAMES = {"background", "bg", "back", "backdrop"}


def _thumb_b64(img: Image.Image, size=(140, 100)) -> str:
    t = img.convert("RGBA").copy()
    t.thumbnail(size, Image.LANCZOS)
    bg = Image.new("RGBA", t.size, (200, 200, 200, 255))
    for y in range(0, t.height, 8):
        for x in range(0, t.width, 8):
            if (x // 8 + y // 8) % 2 == 0:
                for py in range(min(8, t.height - y)):
                    for px in range(min(8, t.width - x)):
                        bg.putpixel((x + px, y + py), (230, 230, 230, 255))
    bg.paste(t, (0, 0), t.split()[3])
    buf = io.BytesIO()
    bg.convert("RGB").save(buf, "JPEG", quality=75)
    return base64.b64encode(buf.getvalue()).decode()


def _get_text_style(layer):
    try:
        td = layer.engine_dict
        style = td["StyleRun"]["RunArray"][0]["StyleSheet"]["StyleSheetData"]
        size = int(style.get("FontSize", 36))
        c = style.get("FillColor", {}).get("Values", [1, 1, 1, 1])
        r, g, b = int(c[1]*255), int(c[2]*255), int(c[3]*255)
        align_raw = td.get("ParagraphRun", {}).get("RunArray", [{}])[0]
        align = align_raw.get("Paragraph", {}).get("Alignment", 0)
        return {
            "size": size,
            "color": (r, g, b),
            "color_hex": "#{:02x}{:02x}{:02x}".format(r, g, b),
            "bold": style.get("FauxBold", False),
            "align": {0: "left", 1: "right", 2: "center"}.get(align, "left"),
        }
    except Exception:
        return {"size": 36, "color": (255, 255, 255), "color_hex": "#ffffff", "bold": False, "align": "center"}


def extract_layers(psd_path: str) -> dict:
    if not HAS_PSD:
        raise RuntimeError("psd-tools not installed")
    psd = PSDImage.open(psd_path)
    W, H = psd.width, psd.height

    # Full composite thumbnail
    try:
        full = psd.composite()
        full_thumb = _thumb_b64(full, (480, 360))
    except Exception:
        full_thumb = None

    def walk(layers, depth=0):
        result = []
        for lyr in layers:
            kind = lyr.kind if hasattr(lyr, "kind") else "unknown"
            is_bg = lyr.name.lower().strip() in BG_NAMES
            info = {
                "name": lyr.name,
                "kind": kind,
                "is_bg": is_bg,
                "bbox": [lyr.left, lyr.top, lyr.right, lyr.bottom],
                "visible": lyr.is_visible() if hasattr(lyr, "is_visible") else True,
                "depth": depth,
                "text": None,
                "text_style": None,
                "thumb": None,
            }
            if kind == TEXT_KIND:
                try:
                    info["text"] = lyr.text
                except Exception:
                    info["text"] = lyr.name
                info["text_style"] = _get_text_style(lyr)
            elif kind in PHOTO_KINDS or (kind == "pixel" and is_bg):
                try:
                    img = lyr.composite()
                    if img:
                        info["thumb"] = _thumb_b64(img)
                except Exception:
                    pass
            result.append(info)
            if hasattr(lyr, "__iter__") and kind == "group":
                result.extend(walk(list(lyr), depth + 1))
        return result

    return {
        "layers": walk(list(psd)),
        "width": W,
        "height": H,
        "full_thumb": full_thumb,
    }


FONT_MAP = {
    "Arial":           {"r":"arial.ttf",    "b":"arialbd.ttf",  "i":"ariali.ttf",   "bi":"arialbi.ttf"},
    "Times New Roman": {"r":"times.ttf",    "b":"timesbd.ttf",  "i":"timesi.ttf",   "bi":"timesbi.ttf"},
    "Calibri":         {"r":"calibri.ttf",  "b":"calibrib.ttf", "i":"calibrii.ttf", "bi":"calibriz.ttf"},
    "Verdana":         {"r":"verdana.ttf",  "b":"verdanab.ttf", "i":"verdanai.ttf", "bi":"verdanaz.ttf"},
    "Georgia":         {"r":"georgia.ttf",  "b":"georgiab.ttf", "i":"georgiai.ttf", "bi":"georgiaz.ttf"},
    "Impact":          {"r":"impact.ttf",   "b":"impact.ttf",   "i":"impact.ttf",   "bi":"impact.ttf"},
    "Comic Sans":      {"r":"comic.ttf",    "b":"comicbd.ttf",  "i":"comic.ttf",    "bi":"comicbd.ttf"},
    "Trebuchet":       {"r":"trebuc.ttf",   "b":"trebucbd.ttf", "i":"trebucit.ttf", "bi":"trebucbi.ttf"},
    "DejaVu":          {"r":"DejaVuSans.ttf","b":"DejaVuSans-Bold.ttf","i":"DejaVuSans-Oblique.ttf","bi":"DejaVuSans-BoldOblique.ttf"},
}

def _font(size, bold=False, italic=False, family="Arial"):
    fm = FONT_MAP.get(family, FONT_MAP["Arial"])
    key = ("bi" if bold and italic else "b" if bold else "i" if italic else "r")
    candidates = [fm[key], fm["b"], fm["r"], "arial.ttf", "DejaVuSans.ttf"]
    for name in candidates:
        try:
            return ImageFont.truetype(name, max(8, size))
        except Exception:
            continue
    return ImageFont.load_default()


def _hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _gradient_img(w, h, top, bot):
    arr = np.zeros((h, w, 3), dtype=np.uint8)
    for i in range(h):
        t = i / h
        arr[i] = [int(top[c] + (bot[c] - top[c]) * t) for c in range(3)]
    return Image.fromarray(arr, "RGB").convert("RGBA")


def _safe_text(lyr):
    try:
        return lyr.text or ""
    except Exception:
        return ""


def _composite_layer_onto(canvas: Image.Image, lyr, W: int, H: int):
    """Composite a single psd-tools layer onto canvas in place. Returns updated canvas."""
    try:
        limg = lyr.composite()
        if limg:
            lrgba = limg.convert("RGBA")
            tmp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            x = max(0, lyr.left)
            y = max(0, lyr.top)
            tmp.paste(lrgba, (x, y), lrgba.split()[3])
            canvas = Image.alpha_composite(canvas, tmp)
    except Exception:
        pass
    return canvas


def render_with_edits(psd_path: str, edits: dict) -> Image.Image:
    """
    Two strategies depending on whether image replacements are present:
    - No image edits: full composite as base, overlay text changes.
    - Image edits present: layer-by-layer composite (bottom→top), swap replaced photo.
    """
    if not HAS_PSD:
        raise RuntimeError("psd-tools not installed")

    psd = PSDImage.open(psd_path)
    W, H = psd.width, psd.height

    text_edits   = edits.get("text_edits", {})
    text_colors  = edits.get("text_colors", {})
    text_sizes   = edits.get("text_sizes", {})
    text_fonts   = edits.get("text_fonts", {})
    text_bolds   = edits.get("text_bolds", {})
    text_italics = edits.get("text_italics", {})
    image_edits  = edits.get("image_edits", {})
    hidden       = set(edits.get("hidden", []))
    bg_color     = edits.get("bg_color")
    bg_gradient  = edits.get("bg_gradient")
    bg_image     = edits.get("bg_image")

    # Flatten layers bottom→top (psd layer list is top→bottom, so reverse)
    def all_layers(layers):
        result = []
        for lyr in layers:
            result.append(lyr)
            if hasattr(lyr, "__iter__") and lyr.kind == "group":
                result.extend(all_layers(list(lyr)))
        return result

    flat_topdown = all_layers(list(psd))
    flat_bottomup = list(reversed(flat_topdown))

    bg_layer_names = {l.name for l in flat_topdown if l.name.lower().strip() in BG_NAMES}

    def scale_fill(photo: Image.Image, bw: int, bh: int) -> Image.Image:
        """Scale photo so it covers bw×bh (no empty bars), center-crop."""
        scale = max(bw / photo.width, bh / photo.height)
        pw = int(photo.width * scale)
        ph = int(photo.height * scale)
        photo = photo.resize((pw, ph), Image.LANCZOS)
        lc = (pw - bw) // 2
        tc = (ph - bh) // 2
        return photo.crop((lc, tc, lc + bw, tc + bh))

    # Names of ALL layers being changed (text + photo + hidden)
    edited_names = set(image_edits) | set(text_edits) | set(text_colors) | set(text_sizes) | hidden

    # ── Try to get base composite WITHOUT edited layers ───────────────────────
    base_without = None
    if edited_names:
        try:
            result = psd.composite(layer_filter=lambda l, en=edited_names: l.name not in en)
            # Verify it actually excluded layers (size check)
            if result and result.size == (W, H):
                base_without = result.convert("RGBA")
        except Exception as ex:
            print(f"layer_filter not supported: {ex}")

    # Fall back to full composite if filter didn't work
    try:
        full_composite = psd.composite().convert("RGBA")
    except Exception:
        full_composite = Image.new("RGBA", (W, H), (255, 255, 255, 255))

    canvas = base_without if base_without else full_composite.copy()

    # ── Background override ───────────────────────────────────────────────────
    if bg_color or bg_gradient or bg_image:
        if bg_image:
            bg = bg_image.convert("RGBA").resize((W, H), Image.LANCZOS)
        elif bg_gradient:
            top_c = _hex_to_rgb(bg_gradient[0])
            bot_c = _hex_to_rgb(bg_gradient[1])
            bg = _gradient_img(W, H, top_c, bot_c)
        else:
            bg = Image.new("RGBA", (W, H), (*_hex_to_rgb(bg_color), 255))
        merged = bg.copy()
        merged = Image.alpha_composite(merged, canvas)
        canvas = merged

    # ── Photo replacements ────────────────────────────────────────────────────
    for name, new_img in image_edits.items():
        lyr = next((l for l in flat_topdown if l.name == name), None)
        if not lyr:
            continue
        bw = max(1, lyr.right - lyr.left)
        bh = max(1, lyr.bottom - lyr.top)

        # If layer_filter didn't work, erase the original photo from canvas first
        if not base_without:
            # Get z-order: layers above (decorations) and below (background)
            lyr_idx = next((i for i, l in enumerate(flat_topdown) if l.name == name), 0)
            above_names = {l.name for l in flat_topdown[:lyr_idx]}
            below_names = {l.name for l in flat_topdown[lyr_idx + 1:]}

            # Try to rebuild canvas without this photo layer
            try:
                without = psd.composite(layer_filter=lambda l, n=name: l.name != n)
                if without and without.size == (W, H):
                    canvas = without.convert("RGBA")
            except Exception:
                # Last resort: sample border pixels to fill photo slot
                # Sample 4-pixel border around slot for background color
                sl, st, sr, sb = lyr.left, lyr.top, lyr.right, lyr.bottom
                border_pixels = []
                for x in range(max(0,sl-2), min(W,sr+2)):
                    if st-1 >= 0: border_pixels.append(full_composite.getpixel((x, max(0,st-1))))
                    if sb+1 < H:  border_pixels.append(full_composite.getpixel((x, min(H-1,sb+1))))
                for y in range(max(0,st-2), min(H,sb+2)):
                    if sl-1 >= 0: border_pixels.append(full_composite.getpixel((max(0,sl-1), y)))
                    if sr+1 < W:  border_pixels.append(full_composite.getpixel((min(W-1,sr+1), y)))
                if border_pixels:
                    avg = tuple(int(sum(p[c] for p in border_pixels)/len(border_pixels)) for c in range(3))
                else:
                    avg = (255, 255, 255)
                fill = Image.new("RGBA", (bw, bh), (*avg, 255))
                canvas.paste(fill, (sl, st))

        photo = scale_fill(new_img.convert("RGBA"), bw, bh)
        # Paste as fully opaque solid (RGB) — guarantees full coverage of anything below
        canvas_rgb = canvas.convert("RGB")
        canvas_rgb.paste(photo.convert("RGB"), (lyr.left, lyr.top))
        canvas = canvas_rgb.convert("RGBA")

        # Re-apply decorations above this layer (balloons, confetti, text overlays)
        if not base_without:
            lyr_idx = next((i for i, l in enumerate(flat_topdown) if l.name == name), 0)
            for above_lyr in flat_topdown[:lyr_idx]:
                try:
                    limg = above_lyr.composite()
                    if limg and above_lyr.name not in hidden:
                        lrgba = limg.convert("RGBA")
                        tmp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                        tmp.paste(lrgba, (above_lyr.left, above_lyr.top), lrgba.split()[3])
                        canvas = Image.alpha_composite(canvas, tmp)
                except Exception:
                    pass

    # ── Text rendering: erase slot cleanly then draw new text ─────────────────
    draw = ImageDraw.Draw(canvas)
    text_layer_names = set(text_edits) | set(text_colors) | set(text_sizes)
    for name in text_layer_names:
        lyr = next((l for l in flat_topdown if l.name == name and l.kind == TEXT_KIND), None)
        if not lyr:
            continue
        try:
            style    = _get_text_style(lyr)
            orig_text = _safe_text(lyr)
            new_text = text_edits.get(name, orig_text) or orig_text or name
            new_size = int(text_sizes.get(name, style["size"]))
            color    = _hex_to_rgb(text_colors[name]) if name in text_colors else style["color"]
            family   = text_fonts.get(name, "Arial")
            bold     = text_bolds.get(name, style.get("bold", False))
            italic   = text_italics.get(name, False)
            font     = _font(max(8, new_size), bold, italic, family)

            bw = max(1, lyr.right - lyr.left)
            bh = max(1, lyr.bottom - lyr.top)
            cx = lyr.left + bw // 2
            cy = lyr.top  + bh // 2

            # Sample background colour from surrounding area for clean erase
            pad = max(new_size // 2, 10)
            sx = max(0, lyr.left - pad);  ex = min(W, lyr.right + pad)
            sy = max(0, lyr.top  - pad);  ey = min(H, lyr.bottom + pad)
            region = canvas.crop((sx, sy, ex, ey))
            # Heavily blur to get the bg tone without text
            erased = region.filter(ImageFilter.GaussianBlur(radius=max(new_size, 20)))
            # Crop back to exact text slot
            inner = erased.crop((lyr.left - sx, lyr.top - sy,
                                  lyr.right - sx, lyr.bottom - sy))
            canvas.paste(inner, (lyr.left, lyr.top))
            draw = ImageDraw.Draw(canvas)  # refresh after paste

            # Word-wrap
            words = new_text.replace("\r", "").split()
            lines, line = [], ""
            for w in words:
                test = (line + " " + w).strip()
                bb = draw.textbbox((0, 0), test, font=font)
                if bb[2] - bb[0] <= max(bw - 10, 60):
                    line = test
                else:
                    if line: lines.append(line)
                    line = w
            if line: lines.append(line)
            if not lines: lines = [new_text]

            line_h = draw.textbbox((0, 0), "Ag", font=font)[3] + 6
            total_h = line_h * len(lines)
            ty = cy - total_h // 2
            align = style.get("align", "center")

            for ln in lines:
                bb = draw.textbbox((0, 0), ln, font=font)
                tw = bb[2] - bb[0]
                tx = (lyr.left if align == "left"
                      else lyr.right - tw if align == "right"
                      else cx - tw // 2)
                draw.text((tx + 2, ty + 2), ln, fill=(0, 0, 0, 130), font=font)
                draw.text((tx, ty), ln, fill=(*color, 255), font=font)
                ty += line_h
        except Exception as e:
            print(f"Text error '{name}': {e}")

    return canvas.convert("RGB")
