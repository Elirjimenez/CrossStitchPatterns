from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen.canvas import Canvas

from app.domain.model.pattern import Pattern
from app.domain.services.fabric import FabricSize

PAGE_W, PAGE_H = A4
MARGIN = 2 * cm


def render_overview_page(
    pattern: Pattern,
    title: str,
    fabric_size: FabricSize,
    aida_count: int,
    margin_cm: float,
) -> bytes:
    buf = BytesIO()
    c = Canvas(buf, pagesize=A4)

    # --- Title ---
    c.setFont("Helvetica-Bold", 24)
    title_y = PAGE_H - MARGIN
    c.drawCentredString(PAGE_W / 2, title_y, title)

    # --- Footer text ---
    stitch_text = f"{pattern.grid.width} x {pattern.grid.height} stitches"
    fabric_text = (
        f"Fabric: {fabric_size.width_cm:.1f} x {fabric_size.height_cm:.1f} cm "
        f"({aida_count}ct Aida, {margin_cm:.1f} cm margin)"
    )

    c.setFont("Helvetica", 11)
    footer_line2_y = MARGIN
    footer_line1_y = footer_line2_y + 16
    c.drawCentredString(PAGE_W / 2, footer_line1_y, stitch_text)
    c.drawCentredString(PAGE_W / 2, footer_line2_y, fabric_text)

    # --- Pattern thumbnail ---
    thumb_top = title_y - 12
    thumb_bottom = footer_line1_y + 16
    avail_w = PAGE_W - 2 * MARGIN
    avail_h = thumb_top - thumb_bottom

    grid = pattern.grid
    aspect = grid.width / grid.height
    if avail_w / avail_h > aspect:
        thumb_h = avail_h
        thumb_w = thumb_h * aspect
    else:
        thumb_w = avail_w
        thumb_h = thumb_w / aspect

    thumb_x = (PAGE_W - thumb_w) / 2
    thumb_y = thumb_bottom + (avail_h - thumb_h) / 2

    cell_w = thumb_w / grid.width
    cell_h = thumb_h / grid.height

    for y, row in enumerate(grid.cells):
        for x, idx in enumerate(row):
            r, g, b = pattern.palette.colors[idx]
            c.setFillColorRGB(r / 255.0, g / 255.0, b / 255.0)
            cx = thumb_x + x * cell_w
            cy = thumb_y + thumb_h - (y + 1) * cell_h
            c.rect(cx, cy, cell_w, cell_h, stroke=0, fill=1)

    c.showPage()
    c.save()
    return buf.getvalue()
