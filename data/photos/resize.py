from pathlib import Path
from PIL import Image, ImageOps

for path in sorted(Path(".").glob("*.jpg")):
    with Image.open(path) as original:
        img = ImageOps.exif_transpose(original).convert("RGB")
    img.thumbnail((512, 512))      # only ever shrinks, keeps the aspect ratio
    img.save(path, quality=85)     # saved without the EXIF metadata
    print(f"{path.name}: {img.size[0]}x{img.size[1]}")
