"""Analyze image — detect dominant theme and extract palette."""
from PIL import Image
import numpy as np
from sklearn.cluster import KMeans


def rgb_to_hsl(r, g, b):
    r, g, b = r / 255, g / 255, b / 255
    mx, mn = max(r, g, b), min(r, g, b)
    l = (mx + mn) / 2
    if mx == mn:
        return 0, 0, l
    d = mx - mn
    s = d / (2 - mx - mn) if l > 0.5 else d / (mx + mn)
    if mx == r:
        h = (g - b) / d + (6 if g < b else 0)
    elif mx == g:
        h = (b - r) / d + 2
    else:
        h = (r - g) / d + 4
    return h * 60, s, l


def extract_palette(img: Image.Image, n: int = 6) -> list[str]:
    small = img.convert("RGB").resize((120, 120))
    pixels = np.array(small).reshape(-1, 3).astype(float)
    km = KMeans(n_clusters=n, n_init=10, random_state=0)
    km.fit(pixels)
    centers = km.cluster_centers_.astype(int)
    labels, counts = np.unique(km.labels_, return_counts=True)
    order = np.argsort(-counts)
    return [f"#{int(centers[i][0]):02x}{int(centers[i][1]):02x}{int(centers[i][2]):02x}"
            for i in order]


def suggest_theme(img: Image.Image) -> str:
    palette = extract_palette(img, n=8)
    scores = {"natural": 0, "wedding": 0, "birthday": 0, "corporate": 0, "elegant": 0}

    for hex_c in palette:
        r, g, b = int(hex_c[1:3], 16), int(hex_c[3:5], 16), int(hex_c[5:7], 16)
        h, s, l = rgb_to_hsl(r, g, b)

        # Very dark → elegant
        if l < 0.2:
            scores["elegant"] += 2
        # White/cream → wedding
        if l > 0.85 and s < 0.25:
            scores["wedding"] += 2
        # Warm gold/cream tones → wedding
        if 25 < h < 55 and s > 0.3 and l > 0.5:
            scores["wedding"] += 1
        # Green tones → natural
        if 70 < h < 160 and s > 0.25:
            scores["natural"] += 2
        # Bright pink/red → birthday
        if (h < 15 or h > 330) and s > 0.6:
            scores["birthday"] += 2
        if 290 < h < 360 and s > 0.5:
            scores["birthday"] += 1
        # Deep blue → corporate
        if 200 < h < 260 and s > 0.4 and l < 0.5:
            scores["corporate"] += 2

    return max(scores, key=scores.get)
