from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import Response, JSONResponse
from PIL import Image
import io, os, base64, uuid

from app.core.extractor import extract_subject, smart_crop_subject
from app.core.renderer import render, render_all_products, PRODUCTS, THEMES
from app.core.analyzer import extract_palette, suggest_theme
from app.core.template_engine import list_templates, render_template, make_collage
from app.core.psd_editor import extract_layers, render_with_edits

router = APIRouter()
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "output")
os.makedirs(OUT_DIR, exist_ok=True)


def _load_image(file: UploadFile) -> Image.Image:
    data = file.file.read()
    fname = (file.filename or "").lower()
    if fname.endswith(".psd"):
        try:
            from psd_tools import PSDImage
            import tempfile, os
            with tempfile.NamedTemporaryFile(suffix=".psd", delete=False) as tmp:
                tmp.write(data)
                tmp_path = tmp.name
            try:
                psd = PSDImage.open(tmp_path)
                return psd.composite().convert("RGBA")
            finally:
                os.unlink(tmp_path)
        except Exception as e:
            raise HTTPException(400, f"Could not open PSD: {e}")
    return Image.open(io.BytesIO(data))


@router.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    img = _load_image(file)
    palette = extract_palette(img)
    theme = suggest_theme(img)
    return {
        "filename": file.filename,
        "size": list(img.size),
        "suggested_theme": theme,
        "palette": palette,
        "available_themes": list(THEMES.keys()),
        "available_products": {k: v["label"] for k, v in PRODUCTS.items()},
    }


@router.post("/extract")
async def extract(file: UploadFile = File(...)):
    img = _load_image(file)
    cutout = extract_subject(img)
    cutout = smart_crop_subject(cutout)
    buf = io.BytesIO()
    cutout.save(buf, "PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return {"image_base64": b64, "size": list(cutout.size)}


@router.post("/render")
async def render_product(
    file: UploadFile = File(...),
    product: str = Form("frame_5x7"),
    theme: str = Form("natural"),
    title: str = Form(""),
    subtitle: str = Form(""),
    extract_bg: bool = Form(True),
    subject_scale: float = Form(0.75),
    subject_x_pct: float = Form(0.5),
    c_bg_top: str = Form(None),
    c_bg_bot: str = Form(None),
    c_text: str = Form(None),
    c_accent: str = Form(None),
    c_border: str = Form(None),
    c_shadow: str = Form(None),
    deco_border: bool = Form(True),
    deco_shadow: bool = Form(True),
    deco_underline: bool = Form(True),
    deco_separator: bool = Form(True),
):
    if product not in PRODUCTS:
        raise HTTPException(400, f"Unknown product: {product}")

    img = _load_image(file)

    if extract_bg:
        subject = extract_subject(img)
        subject = smart_crop_subject(subject)
    else:
        subject = img.convert("RGBA")

    custom_colors = {k: v for k, v in {
        "bg_top": c_bg_top, "bg_bot": c_bg_bot,
        "text": c_text, "accent": c_accent,
        "border": c_border, "text_shadow": c_shadow,
    }.items() if v}

    decos = {
        "border": deco_border, "shadow": deco_shadow,
        "underline": deco_underline, "separator": deco_separator,
    }

    result = render(subject, product, theme, title, subtitle,
                    subject_scale=subject_scale, subject_x_pct=subject_x_pct,
                    custom_colors=custom_colors, decos=decos)

    buf = io.BytesIO()
    result.save(buf, "PNG", dpi=(300, 300))
    buf.seek(0)
    return Response(content=buf.read(), media_type="image/png")


@router.post("/batch")
async def batch_render(
    file: UploadFile = File(...),
    theme: str = Form("natural"),
    title: str = Form(""),
    subtitle: str = Form(""),
    extract_bg: bool = Form(True),
):
    img = _load_image(file)

    if extract_bg:
        subject = extract_subject(img)
        subject = smart_crop_subject(subject)
    else:
        subject = img.convert("RGBA")

    session_id = str(uuid.uuid4())[:8]
    out_dir = os.path.join(OUT_DIR, session_id)
    results = render_all_products(subject, theme, title, subtitle, out_dir)

    return {
        "session": session_id,
        "output_dir": out_dir,
        "results": results,
        "total": len([r for r in results.values() if r["status"] == "ok"]),
    }


@router.get("/products")
def list_products():
    return {"products": {k: v["label"] for k, v in PRODUCTS.items()}}


@router.get("/themes")
def list_themes():
    return {"themes": list(THEMES.keys())}


@router.get("/templates")
def get_templates():
    templates = list_templates()
    # Strip internal psd_path from response
    safe = [{k: v for k, v in t.items() if k != "psd_path"} for t in templates]
    return {"templates": safe}


@router.post("/render-template")
async def render_psd_template(
    file: UploadFile = File(...),
    template_id: str = Form(...),
    extract_bg: bool = Form(True),
):
    """Replace photo placeholder in a PSD template with user photo."""
    templates = list_templates()
    match = next((t for t in templates if t["id"] == template_id), None)
    if not match:
        raise HTTPException(404, f"Template not found: {template_id}")

    img = _load_image(file)

    if extract_bg:
        subject = extract_subject(img)
        subject = smart_crop_subject(subject)
    else:
        subject = img.convert("RGBA")

    result = render_template(match["psd_path"], subject)

    buf = io.BytesIO()
    result.save(buf, "PNG", dpi=(300, 300))
    buf.seek(0)
    return Response(content=buf.read(), media_type="image/png")


@router.post("/psd-layers")
async def psd_layers(file: UploadFile = File(...)):
    import tempfile, os as _os
    data = file.file.read()
    with tempfile.NamedTemporaryFile(suffix=".psd", delete=False) as tmp:
        tmp.write(data); tmp_path = tmp.name
    try:
        result = extract_layers(tmp_path)
    finally:
        _os.unlink(tmp_path)
    result["filename"] = file.filename
    return result


@router.post("/psd-render")
async def psd_render(
    psd_file: UploadFile = File(...),
    text_edits:   str = Form("{}"),
    text_colors:  str = Form("{}"),
    text_sizes:   str = Form("{}"),
    text_fonts:   str = Form("{}"),
    text_bolds:   str = Form("{}"),
    text_italics: str = Form("{}"),
    image_files:  list[UploadFile] = File(default=[]),
    image_names:  str = Form("[]"),
    extract_bgs:  str = Form("[]"),   # [bool] matching image_files
    bg_color:     str = Form(None),
    bg_gradient:  str = Form(None),   # JSON [top_hex, bot_hex]
    bg_image_file: UploadFile = File(default=None),
    hidden:       str = Form("[]"),
):
    import json, tempfile, os as _os
    data = psd_file.file.read()
    with tempfile.NamedTemporaryFile(suffix=".psd", delete=False) as tmp:
        tmp.write(data); tmp_path = tmp.name

    try:
        names = json.loads(image_names)
        do_extract = json.loads(extract_bgs)
        images = {}
        for i, f in enumerate(image_files):
            if i < len(names):
                img = Image.open(io.BytesIO(f.file.read())).convert("RGBA")
                if i < len(do_extract) and do_extract[i]:
                    from app.core.extractor import extract_subject, smart_crop_subject
                    img = extract_subject(img)
                    img = smart_crop_subject(img)
                images[names[i]] = img

        bg_img = None
        if bg_image_file and bg_image_file.filename:
            bg_img = Image.open(io.BytesIO(bg_image_file.file.read())).convert("RGBA")

        edits = {
            "text_edits":   json.loads(text_edits),
            "text_colors":  json.loads(text_colors),
            "text_sizes":   {k: int(v) for k, v in json.loads(text_sizes).items()},
            "text_fonts":   json.loads(text_fonts),
            "text_bolds":   json.loads(text_bolds),
            "text_italics": json.loads(text_italics),
            "image_edits":  images,
            "hidden":       json.loads(hidden),
            "bg_color":     bg_color or None,
            "bg_gradient":  json.loads(bg_gradient) if bg_gradient else None,
            "bg_image":     bg_img,
        }
        try:
            result = render_with_edits(tmp_path, edits)
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise HTTPException(500, f"Render failed: {e}")
    finally:
        _os.unlink(tmp_path)

    buf = io.BytesIO()
    result.save(buf, "PNG", dpi=(300, 300))
    buf.seek(0)
    return Response(content=buf.read(), media_type="image/png")


@router.post("/collage")
async def collage_render(
    files: list[UploadFile] = File(...),
    layout: str = Form("grid"),
    extract_bg: bool = Form(False),
):
    """Combine multiple photos into a collage."""
    if not files:
        raise HTTPException(400, "No files provided")

    photos = []
    for f in files:
        img = Image.open(io.BytesIO(f.file.read()))
        if extract_bg:
            img = extract_subject(img)
            img = smart_crop_subject(img)
        photos.append(img.convert("RGBA"))

    result = make_collage(photos, layout)

    buf = io.BytesIO()
    result.save(buf, "PNG")
    buf.seek(0)
    return Response(content=buf.read(), media_type="image/png")
