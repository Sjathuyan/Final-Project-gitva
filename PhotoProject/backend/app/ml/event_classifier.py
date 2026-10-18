from PIL import Image
import numpy as np
from sklearn.cluster import KMeans

# Rule-based classifier using color palette analysis
# Can be upgraded to CNN model later

THEME_PROFILES = {
    "wedding": {
        "keywords": ["white", "gold", "pink", "cream"],
        "hue_range": [(0, 30), (300, 360)],   # warm/pink hues
    },
    "birthday": {
        "keywords": ["colorful", "bright", "multi"],
        "hue_range": [(0, 360)],               # any hue, high saturation
    },
    "nature": {
        "keywords": ["green", "blue", "brown"],
        "hue_range": [(60, 180)],              # green to cyan
    },
    "graduation": {
        "keywords": ["blue", "gold", "black"],
        "hue_range": [(200, 260)],
    },
}

def rgb_to_hsv(r, g, b):
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    mx = max(r, g, b)
    mn = min(r, g, b)
    diff = mx - mn
    h = 0
    if diff != 0:
        if mx == r:
            h = (60 * ((g - b) / diff) + 360) % 360
        elif mx == g:
            h = (60 * ((b - r) / diff) + 120) % 360
        else:
            h = (60 * ((r - g) / diff) + 240) % 360
    s = 0 if mx == 0 else diff / mx
    v = mx
    return h, s, v

def classify_event(img: Image.Image) -> dict:
    img_rgb = img.convert("RGB").resize((100, 100))
    pixels = np.array(img_rgb).reshape(-1, 3)
    kmeans = KMeans(n_clusters=5, n_init=10, random_state=42)
    kmeans.fit(pixels)
    dominant = kmeans.cluster_centers_.astype(int)

    scores = {theme: 0 for theme in THEME_PROFILES}

    for r, g, b in dominant:
        h, s, v = rgb_to_hsv(r, g, b)
        # High saturation + varied hues = birthday
        if s > 0.5:
            scores["birthday"] += 1
        # White/cream tones = wedding
        if v > 0.85 and s < 0.2:
            scores["wedding"] += 2
        # Green tones = nature
        if 60 <= h <= 180 and s > 0.3:
            scores["nature"] += 2
        # Blue/gold = graduation
        if 200 <= h <= 260:
            scores["graduation"] += 1

    detected = max(scores, key=scores.get)
    confidence = round(scores[detected] / (sum(scores.values()) + 1e-5), 2)

    return {
        "event": detected,
        "confidence": confidence,
        "scores": scores,
        "palette": [f"#{r:02x}{g:02x}{b:02x}" for r, g, b in dominant],
    }
