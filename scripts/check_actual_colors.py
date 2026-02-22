"""
Run each demo project config through the local pattern converter to find
the actual number of DMC colours returned after palette capping.
Does not create any projects or touch the database.
"""
import sys
sys.path.insert(0, ".")

from pathlib import Path
from app.infrastructure.image_processing.pillow_image_resizer import PillowImageResizer
from app.application.use_cases.convert_image_to_pattern import (
    ConvertImageToPattern,
    ConvertImageRequest,
)

ASSETS = Path("tests/assets/official_set")

# (name, filename, target_w, target_h, num_colors, mode)
# note: variant (color/bw) affects CompleteExistingProject but not ConvertImageToPattern
CONFIGS = [
    ("Pixel Art Character",    "07_pixel_art_character.png", 256, 256,  8, "pixel_art"),
    ("Heart B&W",              "01_heart_pixel.png",         256, 256,  4, "drawing"),
    ("Rainbow Cupcake",        "06_rainbow_cupcake.png",     300, 300, 14, "drawing"),
    ("Cartoon Cat",            "02_cartoon_cat.png",         300, 300,  7, "drawing"),
    ("Photo High Detail",      "08_photo.png",               300, 200, 20, "photo"),
    ("Grayscale Portrait",     "10_grayscale_portrait.png",  300, 300,  8, "photo"),
    ("Flower Auto Mode",       "03_flower.png",              200, 200, 11, "auto"),
    ("Dog Silhouette Resized", "04_dog_silhouette.png",       80,  80, 10, "drawing"),
]

resizer = PillowImageResizer()
use_case = ConvertImageToPattern(image_resizer=resizer)

print(f"{'Project':<26} {'Req':>4} {'Got':>4}  {'Size':>9}  {'Stitches':>9}")
print("-" * 65)
for name, fname, tw, th, num_colors, mode in CONFIGS:
    img_path = ASSETS / fname
    with open(img_path, "rb") as f:
        image_data = f.read()

    req = ConvertImageRequest(
        image_data=image_data,
        num_colors=num_colors,
        target_width=tw,
        target_height=th,
        processing_mode=mode,
    )
    result = use_case.execute(req)
    actual = len(result.dmc_colors)
    w = result.pattern.grid.width
    h = result.pattern.grid.height
    stitches = w * h
    print(f"{name:<26} {num_colors:>4} {actual:>4}  {w}x{h:>4}  {stitches:>9}")
