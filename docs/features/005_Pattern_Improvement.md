# Pattern Improvements Plan

## Context
After testing the pattern generator with real images, five improvements are needed:
1. Legend pages should appear after the grid pages, not before them
2. Grid cell size should scale down (5mm to 3mm) for large patterns to reduce page count
3. 10-stitch marker lines need to be thicker, with stitch numbers centered on the line
4. A confetti-reduction step is needed to clean up isolated mismatched pixels
5. Design size (width/height) should be optional, defaulting to the image's native dimensions

Branch: `feature/pattern-improvements` (already created)

---

## 1. Move Legend to End of PDF

**Files to modify:**
- `app/infrastructure/pdf_export/pdf_generator.py` (line 178-179): swap order so grid pages render before legend
- `app/application/use_cases/export_pattern_to_pdf.py` (line 102): page count formula stays the same (2 + grid pages)
- `tests/unit/test_pdf_legend.py`: update test that checks 2-page structure (now legend is last)
- `tests/integration/test_export_pdf_content.py`: may need minor adjustment
- `tests/integration/test_pdf_export_api.py`: page count stays the same

**Changes:**
In `render_pattern_pdf()`, reorder calls:
```python
_draw_overview_page(...)
# Grid pages FIRST
if symbols and tiles:
    for i, tile in enumerate(tiles):
        _draw_grid_page(...)
# Legend LAST
_draw_legend_page(...)
```

---

## 2. Dynamic Cell Size Based on Pattern Dimensions

**Files to modify:**
- `app/domain/services/pattern_tiling.py`: add `compute_cell_size_mm()` function
- `app/application/use_cases/export_pattern_to_pdf.py`: compute cell_size and pass dynamic cols/rows per page
- `app/application/ports/pattern_pdf_exporter.py`: add `cell_size_mm` parameter to `render()` protocol
- `app/infrastructure/pdf_export/pattern_pdf_exporter.py`: pass cell_size_mm through
- `app/infrastructure/pdf_export/pdf_generator.py`: accept and forward cell_size_mm
- `app/infrastructure/pdf_export/pattern_renderer.py`: use dynamic cell size instead of hardcoded constant
- Tests: add tests for `compute_cell_size_mm()`, update existing tests

**Logic for `compute_cell_size_mm()`:**
```python
def compute_cell_size_mm(grid_width: int, grid_height: int) -> float:
    """Return cell size in mm: 5.0 for small, down to 3.0 for large patterns."""
    MAX_CELL = 5.0
    MIN_CELL = 3.0
    # Compute pages at 5mm to decide
    cols_at_max = _cols_per_page(MAX_CELL)
    rows_at_max = _rows_per_page(MAX_CELL)
    pages = ceil(grid_width / cols_at_max) * ceil(grid_height / rows_at_max)

    if pages <= 4:
        return MAX_CELL
    if pages >= 20:
        return MIN_CELL
    # Linear interpolation between 4 and 20 pages
    t = (pages - 4) / (20 - 4)
    return MAX_CELL - t * (MAX_CELL - MIN_CELL)
```

Helper functions compute cols/rows per page given a cell size:
```python
def _cols_per_page(cell_mm: float) -> int:
    cell_pt = cell_mm * 2.8346  # mm to points
    available = PAGE_W - 2 * MARGIN - LABEL_MARGIN_LEFT
    return int(available / cell_pt)

def _rows_per_page(cell_mm: float) -> int:
    cell_pt = cell_mm * 2.8346
    available = PAGE_H - 2 * MARGIN - LABEL_MARGIN_TOP - FOOTER_HEIGHT
    return int(available / cell_pt)
```

The cell size also affects font sizes (scale proportionally):
- SYMBOL_FONT_SIZE: scale from 8pt at 5mm to ~5pt at 3mm
- LABEL_FONT_SIZE: scale from 7pt at 5mm to ~5pt at 3mm

---

## 3. Thicker 10-Stitch Lines + Centered Numbers

**Files to modify:**
- `app/infrastructure/pdf_export/pattern_renderer.py`

**Changes:**
- Increase `THICK_LINE` from `1.2` to `2.0` (or make it relative to cell size)
- Column numbers: currently at `x0 + col * CELL_SIZE + CELL_SIZE / 2` (center of the cell before the line). Move to `x0 + (col + 1) * CELL_SIZE` — aligned with the thick line, but still **outside the grid** (above it for columns, left for rows). **User confirmed: on the line, outside grid.**
- Row numbers: similarly, move to be centered on the thick line position, outside the grid
- Tests: update `test_pattern_renderer.py` if stitch number checks need adjustment

---

## 4. Confetti Reduction (Mode Filter)

**New file:**
- `app/domain/services/confetti.py`: pure domain service

**Files to modify:**
- `app/application/use_cases/convert_image_to_pattern.py`: call confetti reduction after `select_palette`

**New test file:**
- `tests/unit/test_confetti.py`

**Algorithm** (`reduce_confetti(cells, num_passes=2)`):
```python
def reduce_confetti(cells: List[List[int]], num_passes: int = 2) -> List[List[int]]:
    """Replace isolated stitches with the most common neighbor color (mode filter)."""
    for _ in range(num_passes):
        new_cells = copy of cells
        for each cell (r, c):
            neighbors = get 8-connected neighbors
            if len(neighbors) >= 3:
                mode_color = most_common(neighbors)
                if cell != mode_color and count(mode_color in neighbors) >= 5:
                    new_cells[r][c] = mode_color
        cells = new_cells
    return cells
```

The threshold (5 out of 8 neighbors must agree) ensures only truly isolated pixels get smoothed while edges are preserved. **User confirmed: moderate 5/8 threshold.**

---

## 5. Optional Design Size (Default to Image Size)

**Files to modify:**
- `app/application/ports/image_resizer.py`: add `get_image_size()` method to protocol
- `app/infrastructure/image_processing/pillow_image_resizer.py`: implement `get_image_size()`
- `app/application/use_cases/convert_image_to_pattern.py`: make `target_width`/`target_height` Optional, resolve from image if None
- `app/web/api/routes/patterns.py`: make `target_width`/`target_height` optional Form params (default=None)
- `scripts/generate_pattern_from_image.py`: make `--w`/`--h` optional
- Tests: add test cases for None dimensions

**Changes to `ConvertImageRequest`:**
```python
@dataclass(frozen=True)
class ConvertImageRequest:
    image_data: bytes
    num_colors: int
    target_width: Optional[int] = None
    target_height: Optional[int] = None
```

**Changes to `ConvertImageToPattern.execute()`:**
```python
def execute(self, request):
    if request.target_width is None or request.target_height is None:
        w, h = self._image_resizer.get_image_size(request.image_data)
        target_width = request.target_width or w
        target_height = request.target_height or h
    else:
        target_width = request.target_width
        target_height = request.target_height

    pixels = self._image_resizer.load_and_resize(request.image_data, target_width, target_height)
    ...
```

---

## Implementation Order

1. **Legend reorder** (simplest, isolated change)
2. **Thicker lines + centered numbers** (small, isolated)
3. **Confetti reduction** (new domain service, clean addition)
4. **Optional design size** (touches API layer)
5. **Dynamic cell size** (most cross-cutting, touches tiling + rendering + use case)

## Verification

After each change:
```bash
pytest -v --tb=short
black app/ tests/
```

Final end-to-end test: run the server and use `scripts/generate_pattern_from_image.py` with a real image to visually verify all 5 improvements.
