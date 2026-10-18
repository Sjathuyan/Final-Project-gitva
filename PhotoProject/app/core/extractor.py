"""Subject extraction from composite banner images."""
from PIL import Image
import io, numpy as np

def extract_subject(img: Image.Image) -> Image.Image:
    """Remove background, return RGBA cutout of the main subject."""
    try:
        from rembg import remove, new_session
        session = new_session("u2net")          # best model for persons
        buf = io.BytesIO()
        img.convert("RGB").save(buf, "PNG")
        result = remove(buf.getvalue(), session=session)
        return Image.open(io.BytesIO(result)).convert("RGBA")
    except Exception as e:
        # Fallback: return original with white bg removed roughly
        return img.convert("RGBA")


def smart_crop_subject(rgba: Image.Image, padding: float = 0.05) -> Image.Image:
    """Crop tight around the non-transparent region with padding."""
    arr = np.array(rgba)
    alpha = arr[:, :, 3]
    rows = np.any(alpha > 10, axis=1)
    cols = np.any(alpha > 10, axis=0)
    if not rows.any():
        return rgba
    rmin, rmax = np.where(rows)[0][[0, -1]]
    cmin, cmax = np.where(cols)[0][[0, -1]]
    h, w = rgba.height, rgba.width
    pad_r = int((rmax - rmin) * padding)
    pad_c = int((cmax - cmin) * padding)
    rmin = max(0, rmin - pad_r)
    rmax = min(h, rmax + pad_r)
    cmin = max(0, cmin - pad_c)
    cmax = min(w, cmax + pad_c)
    return rgba.crop((cmin, rmin, cmax, rmax))
