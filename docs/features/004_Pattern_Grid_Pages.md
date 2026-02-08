# Plan: PDF Export — Feature 3: Pattern Grid Pages

## Context

Features 1 (Overview) and 2 (Legend) are merged. The PDF currently has 2 pages (overview + legend). Feature 3 adds the **actual printable cross-stitch grid** — the core output of the application. The grid may span multiple pages depending on pattern size.

**Branch:** `feature/pdf-pattern-pages` (already created from latest `main`)

## Design Decisions (Confirmed)

- **Page**: A4 Portrait (matches existing pages)
- **Cell size**: 5mm (~14.17pt) — readable symbols, ~30×46 stitches/page
- **Color variant**: Full palette color fill + auto-contrast symbol (white on dark, black on light)
- **B/W variant**: White cells, black symbols
- **Center marking**: Red lines between the 2 middle rows/columns (cross between 4 center cells)
- **Numbering**: Top + Left edges only, starting at 10 (10, 20, 30...)
- **File structure**: New `app/infrastructure/pdf_export/pattern_renderer.py` for grid rendering
- **Page numbering**: "Page 3/14" at bottom-right (counts only grid pages, not overview/legend)

## Computed Layout Constants

```
A4 = 595.28 × 841.89 pt
MARGIN = 2cm = 56.69pt
CELL_SIZE = 5mm ≈ 14.17pt

Usable area = 481.9 × 728.5 pt

Reserve for labels:
  Left (row numbers):  ~28pt (3-digit numbers in 8pt font)
  Top (col numbers):   ~14pt (numbers above grid)
  Bottom (page number): ~14pt

Grid area = (481.9 - 28) × (728.5 - 14 - 14) = 453.9 × 700.5 pt

Stitches per page:
  cols_per_page = floor(453.9 / 14.17) = 32
  rows_per_page = floor(700.5 / 14.17) = 49

Example — 60×45 sample pattern:
  Pages wide = ceil(60/32) = 2
  Pages tall = ceil(45/49) = 1
  Grid pages = 2, Total PDF pages = 4 (overview + legend + 2 grid)
```

## Architecture

```
Domain (pattern_tiling.py):
  PageTile — dataclass with page coords, global offsets, center-line info
  compute_tiles() — pure math, splits grid into page-sized tiles

Domain (symbol_map.py):
  contrast_color(r, g, b) — returns black or white RGB for text readability

Infrastructure (pattern_renderer.py):  NEW
  _draw_grid_page() — renders one tile: cells, symbols, grid lines, numbering, center lines
  render_grid_pages() — iterates tiles, draws each page on Canvas

Infrastructure (pdf_generator.py):  MODIFY
  render_pattern_pdf() — update to accept grid-page data and append grid pages after legend

Application (export_pattern_to_pdf.py):  MODIFY
  Orchestrate tiling + build grid page data, pass to renderer
  Update num_pages = 2 + len(tiles)
```

## Implementation Steps (TDD)

### Step 1: Domain — Pattern Tiling Engine

**Test:** `tests/unit/test_pattern_tiling.py` (new file)
- Small pattern (4×3, cols_per_page=32, rows_per_page=49) → 1 tile
- Wide pattern (60×45, 32, 49) → 2 tiles (2 cols × 1 row)
- Large pattern (100×100, 32, 49) → 8 tiles (4 cols × 3 rows)
- Edge tile has correct reduced width/height
- Tiles sorted by row then column (reading order)
- Center line info: 60-wide pattern → center_col = 30 (between cols 29–30)
- Even-dimension center falls between two cells
- Center line present only on tile(s) that contain it
- Rejects invalid inputs (zero dimensions, zero per-page)

**Implement:** `app/domain/services/pattern_tiling.py`
```
python
@dataclass(frozen=True)
class PageTile:
    page_index: int       # 0-based, reading order (left→right, top→bottom)
    col_start: int        # global stitch column (0-based, inclusive)
    col_end: int          # exclusive
    row_start: int        # global stitch row (0-based, inclusive)
    row_end: int          # exclusive
    center_col: int | None  # local x where vertical center line falls, or None
    center_row: int | None  # local y where horizontal center line falls, or None

@dataclass(frozen=True)
class TilingResult:
    tiles: List[PageTile]
    total_pages: int
    cols_per_page: int
    rows_per_page: int

def compute_tiles(
    grid_width: int,
    grid_height: int,
    cols_per_page: int,
    rows_per_page: int,
) -> TilingResult
```

Center calculation: `center_col_global = grid_width / 2` (float). The center line falls between stitch `floor(center) - 1` and `floor(center)`. A tile contains this line if `col_start < grid_width / 2 <= col_end`. Local position = `grid_width / 2 - col_start`.

### Step 2: Domain — Contrast Color Utility

**Test:** `tests/unit/test_symbol_map.py` (add to existing file)
- `contrast_color(0, 0, 0)` → `(255, 255, 255)` (white on black)
- `contrast_color(255, 255, 255)` → `(0, 0, 0)` (black on white)
- `contrast_color(255, 0, 0)` → `(255, 255, 255)` (white on red — red is dark)
- `contrast_color(255, 255, 0)` → `(0, 0, 0)` (black on yellow — yellow is light)

**Implement:** Add to `app/domain/services/symbol_map.py`
```python
from app.domain.model.pattern import RGB

def contrast_color(r: int, g: int, b: int) -> RGB:
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
    return (255, 255, 255) if luminance < 0.5 else (0, 0, 0)
```

### Step 3: Infrastructure — Grid Page Renderer (B/W first)

**Test:** `tests/unit/test_pattern_renderer.py` (new file)
- `render_grid_pages()` returns valid PDF bytes
- 4×3 pattern (1 tile) → 1 page
- 60×45 pattern (2 tiles) → 2 pages
- B/W page contains symbol text (extracted via pypdf)
- Page contains stitch number text (e.g. "10", "20")
- Page contains page number text (e.g. "1 / 2")

**Implement:** `app/infrastructure/pdf_export/pattern_renderer.py`

```
python
CELL_SIZE = 5 * mm           # 5mm ≈ 14.17pt
SYMBOL_FONT_SIZE = 8         # 8pt fits inside 14pt cell
LABEL_FONT_SIZE = 7
THIN_LINE = 0.3
THICK_LINE = 1.2
CENTER_LINE = 1.5
LABEL_MARGIN_LEFT = 28       # space for row numbers
LABEL_MARGIN_TOP = 14        # space for col numbers

def _draw_grid_page(
    c: Canvas,
    pattern: Pattern,
    symbols: List[str],
    tile: PageTile,
    page_num: int,          # 1-based
    total_grid_pages: int,
    variant: str,           # "color" or "bw"
) -> None

def render_grid_pages(
    pattern: Pattern,
    symbols: List[str],
    tiles: List[PageTile],
    variant: str,
) -> bytes  # standalone PDF with just grid pages (for testing)
```

`_draw_grid_page` renders one tile:
1. Compute grid origin: `x0 = MARGIN + LABEL_MARGIN_LEFT`, `y0_top = PAGE_H - MARGIN - LABEL_MARGIN_TOP`
2. For each cell in tile:
   - If color variant: fill rect with palette color
   - Draw symbol centered in cell (contrast color for "color", black for "bw")
3. Draw thin grid lines between all cells
4. Draw thick grid lines every 10 stitches (using global coordinates)
5. Draw center lines (red, CENTER_LINE width) if tile has center_col/center_row
6. Draw stitch numbers: top edge and left edge, every 10th global stitch
7. Draw page footer: "Page X / Y" at bottom-right

### Step 4: Infrastructure — Color Variant Support

Already handled in Step 3 via the `variant` parameter. The contrast_color utility from Step 2 is used when `variant == "color"`.

### Step 5: Integration — Update PDF Assembly

**Test:** Update `tests/unit/use_cases/test_export_pattern_to_pdf.py`
- `num_pages` for 4×3 pattern (1 grid tile) → 3 (overview + legend + 1 grid page)
- PDF contains grid page with symbol text

**Test:** Update `tests/integration/test_pdf_export_api.py`
- Response PDF has 3+ pages

**Implement:** Modify `app/infrastructure/pdf_export/pdf_generator.py`
- `render_pattern_pdf()` gains new params: `symbols`, `tiles`, `variant`
- After legend page, calls `_draw_grid_page()` for each tile on the shared Canvas
- Import `_draw_grid_page` from `pattern_renderer`

**Implement:** Modify `app/application/use_cases/export_pattern_to_pdf.py`
- Import `compute_tiles` from `pattern_tiling`
- Compute tiles with `cols_per_page=32`, `rows_per_page=49`
- Pass `symbols`, `tiles`, `variant` to `render_pattern_pdf()`
- Return `num_pages = 2 + tiling.total_pages`

### Step 6: Verify & Sample PDF
```bash
pytest -v
pytest --cov=app tests/ -v
black --check app/ tests/
```
Regenerate `sample_overview.pdf` with the full multi-page output.

## Files Changed/Created

| File | Action |
|------|--------|
| `app/domain/services/pattern_tiling.py` | CREATE — `PageTile`, `TilingResult`, `compute_tiles()` |
| `app/domain/services/symbol_map.py` | MODIFY — add `contrast_color()` |
| `app/infrastructure/pdf_export/pattern_renderer.py` | CREATE — `_draw_grid_page()`, `render_grid_pages()` |
| `app/infrastructure/pdf_export/pdf_generator.py` | MODIFY — update `render_pattern_pdf()` to include grid pages |
| `app/application/use_cases/export_pattern_to_pdf.py` | MODIFY — compute tiles, pass to renderer |
| `tests/unit/test_pattern_tiling.py` | CREATE — tiling tests |
| `tests/unit/test_symbol_map.py` | MODIFY — add contrast_color tests |
| `tests/unit/test_pattern_renderer.py` | CREATE — grid rendering tests |
| `tests/unit/use_cases/test_export_pattern_to_pdf.py` | MODIFY — update num_pages |
| `tests/integration/test_pdf_export_api.py` | MODIFY — update page count assertion |

## What Does NOT Change
- `pattern.py`, `stitch_count.py`, `floss.py` — unchanged
- `render_overview_page()` — unchanged
- `_draw_overview_page()`, `_draw_legend_page()` — unchanged
- Web layer, config, domain models — unchanged
- All existing 98 tests pass (except use case + integration tests updating num_pages)
