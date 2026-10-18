from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import photos, themes, products

app = FastAPI(title="Photo Print Studio API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(photos.router, prefix="/api/photos", tags=["Photos"])
app.include_router(themes.router, prefix="/api/themes", tags=["Themes"])
app.include_router(products.router, prefix="/api/products", tags=["Products"])

@app.get("/")
def root():
    return {"status": "Photo Print Studio running"}
