from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from PIL import Image
import io, base64

from app.ml.event_classifier import classify_event
from app.services.color_extractor import extract_palette

router = APIRouter()

@router.post("/analyze")
async def analyze_photo(file: UploadFile = File(...)):
    try:
        data = await file.read()
        img = Image.open(io.BytesIO(data))
        event_info = classify_event(img)
        palette = extract_palette(img)
        return {
            "filename": file.filename,
            "size": img.size,
            "event": event_info["event"],
            "confidence": event_info["confidence"],
            "scores": event_info["scores"],
            "palette": palette,
            "detected_palette": event_info["palette"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/remove-bg")
async def remove_bg(file: UploadFile = File(...)):
    try:
        from app.services.bg_remover import remove_background
        data = await file.read()
        result = remove_background(data)
        b64 = base64.b64encode(result).decode()
        return {"image_base64": b64, "format": "png"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
