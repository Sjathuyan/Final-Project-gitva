from fastapi import APIRouter
from app.themes.theme_engine import THEME_COLORS, PRODUCT_SIZES

router = APIRouter()

@router.get("/list")
def list_themes():
    return {"themes": list(THEME_COLORS.keys())}

@router.get("/products")
def list_products():
    return {"products": list(PRODUCT_SIZES.keys())}

@router.get("/{theme}")
def get_theme(theme: str):
    if theme not in THEME_COLORS:
        return {"error": "Theme not found"}
    return {"theme": theme, "colors": THEME_COLORS[theme]}
