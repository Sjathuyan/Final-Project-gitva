from PIL import Image
import numpy as np
from sklearn.cluster import KMeans

def extract_palette(img: Image.Image, n_colors: int = 5) -> list[str]:
    img_rgb = img.convert("RGB").resize((150, 150))
    pixels = np.array(img_rgb).reshape(-1, 3)
    kmeans = KMeans(n_clusters=n_colors, n_init=10, random_state=42)
    kmeans.fit(pixels)
    colors = kmeans.cluster_centers_.astype(int)
    return [f"#{r:02x}{g:02x}{b:02x}" for r, g, b in colors]

def dominant_color(img: Image.Image) -> str:
    return extract_palette(img, n_colors=1)[0]
