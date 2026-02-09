from __future__ import annotations

from io import BytesIO
from typing import List

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas

from app.domain.model.pattern import Pattern
from app.domain.services.pattern_tiling import PageTile
from app.domain.services.symbol_map import contrast_color

PAGE_W, PAGE_H = A4
MARGIN = 56.69  # 2cm in points

DEFAULT_CELL_MM = 5.0
CELL_SIZE = DEFAULT_CELL_MM * mm  # ~14.17pt (default, used by render_grid_pages)
SYMBOL_FONT_SIZE = 8
LABEL_FONT_SIZE = 9
THIN_LINE = 0.3
THICK_LINE = 2.0
CENTER_LINE_WIDTH = 1.5
LABEL_MARGIN_LEFT = 28  # space for row numbers
LABEL_MARGIN_TOP = 14  # space for col numbers
FOOTER_HEIGHT = 14  # space for page number


def _register_symbol_font() -> str:
    """Register a Unicode-capable font if available, fall back to Helvetica."""
    try:
        pdfmetrics.getFont("DejaVuSans")
        return "DejaVuSans"
    except KeyError:
        pass
    try:
        pdfmetrics.registerFont(TTFont("DejaVuSans", "DejaVuSans.ttf"))
        return "DejaVuSans"
    except Exception:
        return "Helvetica"


_SYMBOL_FONT: str | None = None


def _get_symbol_font() -> str:
    global _SYMBOL_FONT
    if _SYMBOL_FONT is None:
        _SYMBOL_FONT = _register_symbol_font()
    return _SYMBOL_FONT


def _draw_grid_page(
    c: Canvas,
    pattern: Pattern,
    symbols: List[str],
    tile: PageTile,
    page_num: int,
    total_grid_pages: int,
    variant: str,
    cell_size_mm: float = DEFAULT_CELL_MM,
) -> None:
    symbol_font = _get_symbol_font()

    # Compute sizes based on dynamic cell size
    cell_pt = cell_size_mm * mm
    scale = cell_size_mm / DEFAULT_CELL_MM
    sym_font_size = max(4, SYMBOL_FONT_SIZE * scale)
    label_font_size = max(4, LABEL_FONT_SIZE * scale)

    # Grid origin: top-left of the grid drawing area
    x0 = MARGIN + LABEL_MARGIN_LEFT
    y0_top = PAGE_H - MARGIN - LABEL_MARGIN_TOP

    tile_cols = tile.col_end - tile.col_start
    tile_rows = tile.row_end - tile.row_start

    # --- Draw cells (fill + symbol) ---
    for local_row in range(tile_rows):
        global_row = tile.row_start + local_row
        for local_col in range(tile_cols):
            global_col = tile.col_start + local_col

            cell_x = x0 + local_col * cell_pt
            # ReportLab y increases upward, so row 0 is at top
            cell_y = y0_top - (local_row + 1) * cell_pt

            palette_idx = pattern.grid.cells[global_row][global_col]
            r, g, b = pattern.palette.colors[palette_idx]
            sym = symbols[palette_idx]

            # Fill cell
            if variant == "color":
                c.setFillColorRGB(r / 255.0, g / 255.0, b / 255.0)
                c.rect(cell_x, cell_y, cell_pt, cell_pt, stroke=0, fill=1)
                # Symbol in contrast color
                cr, cg, cb = contrast_color(r, g, b)
                c.setFillColorRGB(cr / 255.0, cg / 255.0, cb / 255.0)
            else:
                # B/W: white fill, black symbol
                c.setFillColorRGB(1, 1, 1)
                c.rect(cell_x, cell_y, cell_pt, cell_pt, stroke=0, fill=1)
                c.setFillColorRGB(0, 0, 0)

            # Draw symbol centered in cell
            c.setFont(symbol_font, sym_font_size)
            text_w = c.stringWidth(sym, symbol_font, sym_font_size)
            text_x = cell_x + (cell_pt - text_w) / 2
            text_y = cell_y + (cell_pt - sym_font_size) / 2
            c.drawString(text_x, text_y, sym)

    # --- Draw grid lines ---
    c.setStrokeColorRGB(0, 0, 0)

    # Thin lines for all cells
    c.setLineWidth(THIN_LINE)
    for col in range(tile_cols + 1):
        lx = x0 + col * cell_pt
        c.line(lx, y0_top, lx, y0_top - tile_rows * cell_pt)
    for row in range(tile_rows + 1):
        ly = y0_top - row * cell_pt
        c.line(x0, ly, x0 + tile_cols * cell_pt, ly)

    # Thick lines every 10 stitches (using global coords)
    c.setLineWidth(THICK_LINE)
    for col in range(tile_cols + 1):
        global_col = tile.col_start + col
        if global_col % 10 == 0:
            lx = x0 + col * cell_pt
            c.line(lx, y0_top, lx, y0_top - tile_rows * cell_pt)
    for row in range(tile_rows + 1):
        global_row = tile.row_start + row
        if global_row % 10 == 0:
            ly = y0_top - row * cell_pt
            c.line(x0, ly, x0 + tile_cols * cell_pt, ly)

    # --- Center lines (red) ---
    if tile.center_col is not None:
        c.setStrokeColorRGB(1, 0, 0)
        c.setLineWidth(CENTER_LINE_WIDTH)
        cx = x0 + tile.center_col * cell_pt
        c.line(cx, y0_top, cx, y0_top - tile_rows * cell_pt)

    if tile.center_row is not None:
        c.setStrokeColorRGB(1, 0, 0)
        c.setLineWidth(CENTER_LINE_WIDTH)
        cy = y0_top - tile.center_row * cell_pt
        c.line(x0, cy, x0 + tile_cols * cell_pt, cy)

    # --- Stitch numbers ---
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica", label_font_size)

    # Top edge: column numbers every 10, centered on the thick line
    for col in range(tile_cols + 1):
        global_col = tile.col_start + col
        if global_col > 0 and global_col % 10 == 0:
            lx = x0 + col * cell_pt
            ly = y0_top + 3
            c.drawCentredString(lx, ly, str(global_col))

    # Left edge: row numbers every 10, centered on the thick line
    for row in range(tile_rows + 1):
        global_row = tile.row_start + row
        if global_row > 0 and global_row % 10 == 0:
            lx = x0 - 4
            ly = y0_top - row * cell_pt - label_font_size / 2
            c.drawRightString(lx, ly, str(global_row))

    # --- Page number footer ---
    c.setFont("Helvetica", 9)
    footer_text = f"{page_num} / {total_grid_pages}"
    c.drawRightString(
        PAGE_W - MARGIN,
        MARGIN - FOOTER_HEIGHT,
        footer_text,
    )

    c.showPage()


def render_grid_pages(
    pattern: Pattern,
    symbols: List[str],
    tiles: List[PageTile],
    variant: str,
    cell_size_mm: float = DEFAULT_CELL_MM,
) -> bytes:
    buf = BytesIO()
    c = Canvas(buf, pagesize=A4)
    total = len(tiles)

    for i, tile in enumerate(tiles):
        _draw_grid_page(c, pattern, symbols, tile, i + 1, total, variant, cell_size_mm)

    c.save()
    return buf.getvalue()
