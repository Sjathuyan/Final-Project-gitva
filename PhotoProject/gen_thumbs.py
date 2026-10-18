from app.core.template_engine import list_templates, THUMB_DIR
from psd_tools import PSDImage
import os

os.makedirs(THUMB_DIR, exist_ok=True)
for t in list_templates():
    thumb_name = f"{t['category']}_{t['name']}.png".replace(' ', '_')
    thumb_path = os.path.join(THUMB_DIR, thumb_name)
    if not os.path.exists(thumb_path):
        try:
            psd = PSDImage.open(t['psd_path'])
            img = psd.composite()
            img.thumbnail((320, 240))
            img.convert('RGB').save(thumb_path, 'PNG')
            print(f"OK: {thumb_name}")
        except Exception as e:
            print(f"FAIL {thumb_name}: {e}")
print("Done")
