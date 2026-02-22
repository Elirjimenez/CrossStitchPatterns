"""
Regenerate the 8 pre-built demo projects on the production Railway instance.

Steps:
  1. Delete all existing projects (clean slate).
  2. Create 8 new projects with revised, higher-quality configurations.
     Most use the source image's native pixel dimensions as stitch dimensions
     (1 pixel = 1 stitch).  Only project 8 uses a custom target size to
     demonstrate the resizing feature.

Usage:
    python scripts/regenerate_demo_projects.py [BASE_URL]

    BASE_URL defaults to the production Railway instance.
"""

import sys
import time
import pathlib
import requests

BASE = sys.argv[1] if len(sys.argv) > 1 else "https://crossstitchpatterns-production.up.railway.app"
ASSETS = pathlib.Path(__file__).parent.parent / "tests" / "assets" / "official_set"

PROJECTS = [
    {
        "name": "Pixel Art Character - Colour",
        "image": "07_pixel_art_character.png",
        "target_width": 256,
        "target_height": 256,
        "num_colors": 8,
        "processing_mode": "pixel_art",
        "variant": "color",
        # 18-count Aida for fine pixel-art detail; compact 3 cm margin
        "aida_count": 18,
        "margin_cm": 3.0,
    },
    {
        "name": "Heart - B&W",
        "image": "01_heart_pixel.png",
        "target_width": 256,
        "target_height": 256,
        "num_colors": 4,
        "processing_mode": "drawing",
        "variant": "bw",
        # Standard 14-count; standard 5 cm margin
        "aida_count": 14,
        "margin_cm": 5.0,
    },
    {
        "name": "Rainbow Cupcake - Rich Colour",
        "image": "06_rainbow_cupcake.png",
        "target_width": 300,
        "target_height": 300,
        "num_colors": 14,
        "processing_mode": "drawing",
        "variant": "color",
        # 11-count (coarser) for a large display piece; wide 7 cm margin
        "aida_count": 11,
        "margin_cm": 7.0,
    },
    {
        "name": "Cartoon Cat - Drawing",
        "image": "02_cartoon_cat.png",
        "target_width": 300,
        "target_height": 300,
        "num_colors": 7,
        "processing_mode": "drawing",
        "variant": "color",
        # 16-count medium-fine fabric; 4 cm margin
        "aida_count": 16,
        "margin_cm": 4.0,
    },
    {
        "name": "Photo - High Detail",
        "image": "08_photo.png",
        "target_width": 300,
        "target_height": 200,
        "num_colors": 20,
        "processing_mode": "photo",
        "variant": "color",
        # Standard 14-count; standard 5 cm margin
        "aida_count": 14,
        "margin_cm": 5.0,
    },
    {
        "name": "Grayscale Portrait - B&W",
        "image": "10_grayscale_portrait.png",
        "target_width": 300,
        "target_height": 300,
        "num_colors": 8,
        "processing_mode": "photo",
        "variant": "bw",
        # 18-count fine Aida for portrait detail; minimal 3 cm margin
        "aida_count": 18,
        "margin_cm": 3.0,
    },
    {
        "name": "Flower - Auto Mode",
        "image": "03_flower.png",
        "target_width": 200,
        "target_height": 200,
        "num_colors": 11,
        "processing_mode": "auto",
        "variant": "color",
        # 20-count finest Aida for delicate floral pattern; 5 cm margin
        "aida_count": 20,
        "margin_cm": 5.0,
    },
    {
        "name": "Dog Silhouette - Resized",
        "image": "04_dog_silhouette.png",
        # Source is 150x150 px; target is 80x80 to demonstrate resizing.
        # 10 colours requested -- system will cap to actual unique colours (~2-3).
        "target_width": 80,
        "target_height": 80,
        "num_colors": 10,
        "processing_mode": "drawing",
        "variant": "color",
        # 11-count coarse fabric suits the bold silhouette; generous 8 cm margin
        "aida_count": 11,
        "margin_cm": 8.0,
    },
]


def delete_all_projects():
    print("\n" + "=" * 60)
    print("Step 1 -- Delete existing projects")
    print("=" * 60)
    r = requests.get(f"{BASE}/api/projects", timeout=30)
    r.raise_for_status()
    projects = r.json()
    if not projects:
        print("  No existing projects found.")
        return
    print(f"  Found {len(projects)} project(s) to delete.")
    for p in projects:
        pid = p["id"]
        name = p.get("name", pid)
        dr = requests.delete(f"{BASE}/hx/projects/{pid}", timeout=30)
        if dr.status_code in (200, 204, 303):
            print(f"  OK  Deleted: {name}")
        else:
            print(f"  ERR Failed to delete '{name}': HTTP {dr.status_code}")
    time.sleep(1)


def create_projects():
    print("\n" + "=" * 60)
    print("Step 2 -- Create 8 demo projects")
    print("=" * 60)
    results = []
    for i, cfg in enumerate(PROJECTS, start=1):
        img_path = ASSETS / cfg["image"]
        if not img_path.exists():
            print(f"  ERR [{i}] Image not found: {img_path}")
            continue

        print(f"\n  [{i}/8] {cfg['name']}")
        print(f"         {cfg['target_width']}x{cfg['target_height']} stitches | "
              f"{cfg['num_colors']} colours | {cfg['processing_mode']} | {cfg['variant']} | "
              f"aida={cfg['aida_count']} | margin={cfg['margin_cm']} cm")

        with open(img_path, "rb") as f:
            files = {"file": (img_path.name, f, "image/png")}
            data = {
                "name": cfg["name"],
                "target_width": cfg["target_width"],
                "target_height": cfg["target_height"],
                "num_colors": cfg["num_colors"],
                "processing_mode": cfg["processing_mode"],
                "variant": cfg["variant"],
                "aida_count": cfg["aida_count"],
                "margin_cm": cfg["margin_cm"],
            }
            try:
                r = requests.post(
                    f"{BASE}/api/projects/complete",
                    files=files,
                    data=data,
                    timeout=180,
                )
                if r.status_code in (200, 201):
                    result = r.json()
                    pid = result.get("project", {}).get("id", "?")
                    pr = result.get("pattern_result", {})
                    actual_colors = len(pr.get("palette", {}).get("colors", []))
                    stitch_count = pr.get("stitch_count", "?")
                    print(f"         OK Created -- project_id={pid}")
                    print(f"            Actual colours: {actual_colors}  |  Stitches: {stitch_count}")
                    results.append((cfg["name"], pid, actual_colors, stitch_count))
                else:
                    print(f"         ERR HTTP {r.status_code}: {r.text[:300]}")
            except requests.exceptions.Timeout:
                print("         ERR Request timed out (>180s)")
            except Exception as exc:
                print(f"         ERR {exc}")

        # Brief pause so the free-tier instance isn't overwhelmed
        time.sleep(3)

    return results


if __name__ == "__main__":
    print(f"Target: {BASE}")
    delete_all_projects()
    summary = create_projects()
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    for name, pid, colours, stitches in summary:
        print(f"  {name}")
        print(f"    project_id={pid}  colours={colours}  stitches={stitches}")
    print(f"\nDone. Browse projects at: {BASE}/projects\n")
