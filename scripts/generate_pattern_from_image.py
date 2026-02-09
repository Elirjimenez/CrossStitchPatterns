import argparse
import json
import os
from pathlib import Path

import requests


def convert_image(
    base_url: str, image_path: Path, target_w: int | None, target_h: int | None, num_colors: int
) -> dict:
    url = f"{base_url}/api/patterns/convert"
    with image_path.open("rb") as f:
        files = {"file": (image_path.name, f, "application/octet-stream")}
        data: dict = {
            "num_colors": str(num_colors),
        }
        if target_w is not None:
            data["target_width"] = str(target_w)
        if target_h is not None:
            data["target_height"] = str(target_h)
        resp = requests.post(url, data=data, files=files, timeout=120)
    resp.raise_for_status()
    return resp.json()


def export_pdf(
    base_url: str,
    convert_payload: dict,
    title: str,
    aida: int,
    strands: int,
    margin_cm: float,
    variant: str,
) -> bytes:
    url = f"{base_url}/api/patterns/export-pdf"

    body = {
        "grid": convert_payload["grid"],
        "palette": convert_payload["palette"],
        "dmc_colors": convert_payload["dmc_colors"],
        "title": title,
        "aida_count": aida,
        "num_strands": strands,
        "margin_cm": margin_cm,
        "variant": variant,  # "color" or "bw"
    }

    resp = requests.post(url, json=body, timeout=180)
    resp.raise_for_status()
    return resp.content


def main():
    parser = argparse.ArgumentParser(
        description="Generate a cross-stitch pattern PDF from a real image via FastAPI endpoints."
    )
    parser.add_argument(
        "--base-url", default="http://127.0.0.1:8000", help="Base URL of the FastAPI server"
    )
    parser.add_argument("--image", required=True, help="Path to input image (png/jpg)")
    parser.add_argument(
        "--w",
        type=int,
        default=None,
        help="Target pattern width (stitches); defaults to image width",
    )
    parser.add_argument(
        "--h",
        type=int,
        default=None,
        help="Target pattern height (stitches); defaults to image height",
    )
    parser.add_argument("--colors", type=int, default=20, help="Number of colors (palette size)")
    parser.add_argument("--title", default="My Pattern", help="Pattern title in the PDF")
    parser.add_argument("--aida", type=int, default=14, help="Aida count (stitches per inch)")
    parser.add_argument("--strands", type=int, default=2, help="Number of strands (1-6)")
    parser.add_argument("--margin-cm", type=float, default=5.0, help="Fabric margin in cm")
    parser.add_argument("--variant", choices=["color", "bw"], default="color", help="PDF variant")
    parser.add_argument(
        "--out", default=None, help="Output PDF path (default: ./out/<name>_<variant>.pdf)"
    )
    parser.add_argument(
        "--save-json", action="store_true", help="Also save convert response JSON next to the PDF"
    )
    args = parser.parse_args()

    image_path = Path(args.image).expanduser().resolve()
    if not image_path.exists():
        raise SystemExit(f"Image not found: {image_path}")

    out_dir = Path("out")
    out_dir.mkdir(exist_ok=True)

    w_label = str(args.w) if args.w else "auto"
    h_label = str(args.h) if args.h else "auto"
    out_pdf = (
        Path(args.out)
        if args.out
        else out_dir / f"{image_path.stem}_{w_label}x{h_label}_{args.variant}.pdf"
    )
    out_pdf = out_pdf.resolve()

    print(
        f"[1/2] Converting image -> grid/palette (w={w_label}, h={h_label}, colors={args.colors})..."
    )
    convert_payload = convert_image(args.base_url, image_path, args.w, args.h, args.colors)

    if args.save_json:
        json_path = out_pdf.with_suffix(".json")
        json_path.write_text(json.dumps(convert_payload, indent=2), encoding="utf-8")
        print(f"Saved JSON: {json_path}")

    print(f"[2/2] Exporting PDF (variant={args.variant})...")
    pdf_bytes = export_pdf(
        args.base_url,
        convert_payload,
        title=args.title,
        aida=args.aida,
        strands=args.strands,
        margin_cm=args.margin_cm,
        variant=args.variant,
    )

    out_pdf.write_bytes(pdf_bytes)
    print(f"Done ✅ PDF saved to: {out_pdf}")


if __name__ == "__main__":
    main()
