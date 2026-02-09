from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional

# Page layout constants (A4 in points)
_PAGE_W = 595.28
_PAGE_H = 841.89
_MARGIN = 56.69  # 2cm
_LABEL_MARGIN_LEFT = 28
_LABEL_MARGIN_TOP = 14
_FOOTER_HEIGHT = 14
_MM_TO_PT = 2.8346


@dataclass(frozen=True)
class PageTile:
    page_index: int
    col_start: int
    col_end: int
    row_start: int
    row_end: int
    center_col: Optional[float]
    center_row: Optional[float]


@dataclass(frozen=True)
class TilingResult:
    tiles: List[PageTile]
    total_pages: int
    cols_per_page: int
    rows_per_page: int


def cols_per_page(cell_mm: float) -> int:
    """Compute how many columns fit on a page given a cell size in mm."""
    cell_pt = cell_mm * _MM_TO_PT
    available = _PAGE_W - 2 * _MARGIN - _LABEL_MARGIN_LEFT
    return int(available / cell_pt)


def rows_per_page(cell_mm: float) -> int:
    """Compute how many rows fit on a page given a cell size in mm."""
    cell_pt = cell_mm * _MM_TO_PT
    available = _PAGE_H - 2 * _MARGIN - _LABEL_MARGIN_TOP - _FOOTER_HEIGHT
    return int(available / cell_pt)


def compute_cell_size_mm(grid_width: int, grid_height: int) -> float:
    """Return cell size in mm: 5.0 for small patterns, down to 3.0 for large ones."""
    MAX_CELL = 5.0
    MIN_CELL = 3.0

    cols_at_max = cols_per_page(MAX_CELL)
    rows_at_max = rows_per_page(MAX_CELL)
    pages = math.ceil(grid_width / cols_at_max) * math.ceil(grid_height / rows_at_max)

    if pages <= 4:
        return MAX_CELL
    if pages >= 20:
        return MIN_CELL
    # Linear interpolation between 4 and 20 pages
    t = (pages - 4) / (20 - 4)
    return round(MAX_CELL - t * (MAX_CELL - MIN_CELL), 2)


def compute_tiles(
    grid_width: int,
    grid_height: int,
    cols_per_page: int,
    rows_per_page: int,
) -> TilingResult:
    if grid_width <= 0 or grid_height <= 0:
        raise ValueError("grid dimensions must be positive")
    if cols_per_page <= 0 or rows_per_page <= 0:
        raise ValueError("per-page dimensions must be positive")

    num_tile_cols = math.ceil(grid_width / cols_per_page)
    num_tile_rows = math.ceil(grid_height / rows_per_page)

    center_col_global = grid_width / 2.0
    center_row_global = grid_height / 2.0

    tiles: List[PageTile] = []
    page_index = 0

    for tr in range(num_tile_rows):
        row_start = tr * rows_per_page
        row_end = min(row_start + rows_per_page, grid_height)

        for tc in range(num_tile_cols):
            col_start = tc * cols_per_page
            col_end = min(col_start + cols_per_page, grid_width)

            # Center line present if it falls within this tile's range
            c_col: Optional[float] = None
            if col_start < center_col_global <= col_end:
                c_col = center_col_global - col_start

            c_row: Optional[float] = None
            if row_start < center_row_global <= row_end:
                c_row = center_row_global - row_start

            tiles.append(
                PageTile(
                    page_index=page_index,
                    col_start=col_start,
                    col_end=col_end,
                    row_start=row_start,
                    row_end=row_end,
                    center_col=c_col,
                    center_row=c_row,
                )
            )
            page_index += 1

    return TilingResult(
        tiles=tiles,
        total_pages=page_index,
        cols_per_page=cols_per_page,
        rows_per_page=rows_per_page,
    )
