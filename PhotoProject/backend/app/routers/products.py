from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import Response
from PIL import Image
import io, os

from app.themes.theme_engine import apply_theme, PRODUCT_SIZES
from app.services import bg_remover as _bg

router = APIRouter()

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

@router.post("/render")
async def render_product(
    file: UploadFile = File(...),
    product: str = Form("frame_4x6"),
    theme: str = Form("wedding"),
    remove_bg: bool = Form(False),
    title_text: str = Form(""),
    custom_bg_color: str = Form(None),
    custom_accent: str = Form(None),
):
    if product not in PRODUCT_SIZES:
        raise HTTPException(status_code=400, detail=f"Unknown product: {product}")

    data = await file.read()
    img = Image.open(io.BytesIO(data))

    if remove_bg:
        img = _bg.remove_background_pil(img)

    result = apply_theme(
        photo=img,
        product=product,
        theme=theme,
        custom_bg_color=custom_bg_color or None,
        custom_accent=custom_accent or None,
        title_text=title_text,
    )

    buf = io.BytesIO()
    result.save(buf, format="PNG", dpi=(300, 300))
    buf.seek(0)
    return Response(content=buf.read(), media_type="image/png")

@router.post("/batch")
async def batch_render(
    file: UploadFile = File(...),
    theme: str = Form("wedding"),
    remove_bg: bool = Form(False),
    title_text: str = Form(""),
):
    data = await file.read()
    img = Image.open(io.BytesIO(data))

    if remove_bg:
        img = remove_background_pil(img)

    results = {}
    for product in PRODUCT_SIZES:
        result = apply_theme(photo=img, product=product, theme=theme, title_text=title_text)
        path = os.path.join(OUTPUT_DIR, f"{product}_{theme}.png")
        result.save(path, format="PNG", dpi=(300, 300))
        results[product] = path

    return {"rendered": results, "count": len(results)}
