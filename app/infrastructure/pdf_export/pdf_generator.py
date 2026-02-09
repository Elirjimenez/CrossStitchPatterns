from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from typing import List

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen.canvas import Canvas

from app.domain.model.pattern import Pattern
from app.domain.services.fabric import FabricSize
from app.domain.services.pattern_tiling import PageTile

PAGE_W, PAGE_H = A4
MARGIN = 2 * cm


@dataclass(frozen=True)
class LegendEntry:
    symbol: str
    dmc_number: str
    dmc_name: str
    r: int
    g: int
    b: int
    stitch_count: int
    skeins: int


def _draw_overview_page(
    c: Canvas,
    pattern: Pattern,
    title: str,
    fabric_size: FabricSize,
    aida_count: int,
    margin_cm: float,
) -> None:
    # --- Title ---
    c.setFont("Helvetica-Bold", 24)
    title_y = PAGE_H - MARGIN
    c.drawCentredString(PAGE_W / 2, title_y, title)

    # --- Footer text ---
    stitch_text = f"Design size: {pattern.grid.width} x {pattern.grid.height} stitches"
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


def _draw_legend_page(c: Canvas, legend_entries: List[LegendEntry]) -> None:
    # --- Title ---
    c.setFont("Helvetica-Bold", 18)
    title_y = PAGE_H - MARGIN
    c.drawCentredString(PAGE_W / 2, title_y, "Legend")

    # --- Table headers ---
    header_y = title_y - 30
    col_symbol = MARGIN
    col_color = MARGIN + 30
    col_dmc = MARGIN + 60
    col_name = MARGIN + 100
    col_stitches = PAGE_W - MARGIN - 100
    col_skeins = PAGE_W - MARGIN - 40

    c.setFont("Helvetica-Bold", 10)
    c.drawString(col_symbol, header_y, "Sym")
    c.drawString(col_color, header_y, "Color")
    c.drawString(col_dmc, header_y, "DMC #")
    c.drawString(col_name, header_y, "Name")
    c.drawString(col_stitches, header_y, "Stitches")
    c.drawString(col_skeins, header_y, "Skeins")

    # --- Header underline ---
    line_y = header_y - 4
    c.setLineWidth(0.5)
    c.line(MARGIN, line_y, PAGE_W - MARGIN, line_y)

    # --- Table rows ---
    row_y = header_y - 20
    row_height = 18
    swatch_size = 10

    c.setFont("Helvetica", 9)
    for entry in legend_entries:
        # Symbol
        c.drawString(col_symbol, row_y, entry.symbol)

        # Color swatch
        c.setFillColorRGB(entry.r / 255.0, entry.g / 255.0, entry.b / 255.0)
        c.rect(col_color, row_y - 2, swatch_size, swatch_size, stroke=1, fill=1)

        # DMC number
        c.setFillColorRGB(0, 0, 0)
        c.drawString(col_dmc, row_y, entry.dmc_number)

        # DMC name
        c.drawString(col_name, row_y, entry.dmc_name)

        # Stitch count
        c.drawString(col_stitches, row_y, str(entry.stitch_count))

        # Skeins
        c.drawString(col_skeins, row_y, str(entry.skeins))

        row_y -= row_height

    c.showPage()


def render_overview_page(
    pattern: Pattern,
    title: str,
    fabric_size: FabricSize,
    aida_count: int,
    margin_cm: float,
) -> bytes:
    buf = BytesIO()
    c = Canvas(buf, pagesize=A4)
    _draw_overview_page(c, pattern, title, fabric_size, aida_count, margin_cm)
    c.save()
    return buf.getvalue()


def render_pattern_pdf(
    pattern: Pattern,
    title: str,
    fabric_size: FabricSize,
    aida_count: int,
    margin_cm: float,
    legend_entries: List[LegendEntry],
    symbols: List[str] | None = None,
    tiles: List[PageTile] | None = None,
    variant: str = "color",
    cell_size_mm: float = 5.0,
) -> bytes:
    from app.infrastructure.pdf_export.pattern_renderer import _draw_grid_page

    buf = BytesIO()
    c = Canvas(buf, pagesize=A4)
    _draw_overview_page(c, pattern, title, fabric_size, aida_count, margin_cm)

    if symbols and tiles:
        total_grid_pages = len(tiles)
        for i, tile in enumerate(tiles):
            _draw_grid_page(
                c, pattern, symbols, tile, i + 1, total_grid_pages, variant, cell_size_mm
            )

    _draw_legend_page(c, legend_entries)

    c.save()
    return buf.getvalue()
