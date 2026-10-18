from PIL import Image
import io

def remove_background(image_bytes: bytes) -> bytes:
    from rembg import remove
    return remove(image_bytes)

def remove_background_pil(img: Image.Image) -> Image.Image:
    from rembg import remove
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    result_bytes = remove(buf.getvalue())
    return Image.open(io.BytesIO(result_bytes)).convert("RGBA")
