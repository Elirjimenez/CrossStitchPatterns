# Plan: PDF Export — Feature 2: Legend Page

## Context

Feature 1 (Overview Page) is merged. The PDF currently renders a single page with a pattern thumbnail and metadata. Feature 2 adds a **legend page** — a table listing every color with its symbol, DMC info, stitch count, and skeins needed. The PDF grows from 1 to 2 pages.

**Branch:** `feature/pdf-legend-page` (from latest `main`)

## Architecture

```
Domain (floss.py):
  compute_per_color_floss()  → per-color skein calculation using actual stitch counts

Infrastructure (pdf_generator.py):
  Refactor to internal _draw_overview_page(canvas, ...) and _draw_legend_page(canvas, ...)
  New render_pattern_pdf() composes both pages into one PDF
  Keep render_overview_page() working (existing tests pass)

Application (export_pattern_to_pdf.py):
  Use case calls render_pattern_pdf() instead of render_overview_page()
  Orchestrates: stitch counting → symbol assignment → per-color floss → PDF render
  Returns num_pages=2
```

## Implementation Steps (TDD)

### Step 1: Domain — Per-Color Floss Calculation

**Test:** `tests/unit/test_floss_estimation.py` (add new tests to existing file)
- `compute_per_color_floss()` with 2 colors, different stitch counts → returns list of `ColorFlossEstimate` with correct skeins per color
- Color with more stitches needs more skeins
- Result sorted by palette_index
- Rejects invalid aida_count / num_strands

**Implement:** Add to `app/domain/services/floss.py`
```python
@dataclass(frozen=True)
class ColorFlossEstimate:
    palette_index: int
    stitch_count: int
    skeins: int

def compute_per_color_floss(
    color_stitch_counts: List[ColorStitchCount],
    aida_count: int,
    num_strands: int = 2,
    margin_ratio: float = 0.2,
) -> List[ColorFlossEstimate]
```
Reuses existing constants (`SKEIN_LENGTH_M`, `STRANDS_PER_SKEIN`, `THREAD_CONSTANT_CM`) and formula from `compute_floss_estimate`, but applies it per-color with actual counts.

### Step 2: Infrastructure — Legend Page Renderer + Multi-Page Composition

**Test:** `tests/unit/test_pdf_legend.py`
- `render_pattern_pdf()` returns bytes starting with `%PDF-`
- PDF has exactly 2 pages (overview + legend)
- Legend page contains "Legend" title text
- Legend page contains DMC number for each color
- Legend page contains DMC name for each color
- Legend page contains stitch count text
- Legend page contains skeins count text

**Implement:** Modify `app/infrastructure/pdf_export/pdf_generator.py`

1. Extract `_draw_overview_page(c: Canvas, ...)` from existing `render_overview_page()` (everything except Canvas creation and save)
2. `render_overview_page()` keeps working by calling the internal helper (existing tests pass)
3. Add `_draw_legend_page(c: Canvas, ...)` — renders legend table:
   - Title "Legend" (Helvetica-Bold 18pt, centered)
   - Table headers: Symbol | Color | DMC # | Name | Stitches | Skeins
   - One row per color: symbol text, colored rect swatch, DMC number, name, count, skeins
   - Font: Helvetica 9-10pt for table rows
4. Add `render_pattern_pdf(...)` — creates one Canvas, calls `_draw_overview_page` + `_draw_legend_page`, returns bytes

**Legend row data type** (passed to renderer):
```python
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
```
Defined in `pdf_generator.py` (infrastructure DTO, not domain).

### Step 3: Use Case — Update ExportPatternToPdf

**Test:** Update `tests/unit/use_cases/test_export_pattern_to_pdf.py`
- `num_pages` is now 2
- PDF bytes contain "Legend" text (extracted via pypdf)

**Implement:** Modify `app/application/use_cases/export_pattern_to_pdf.py`
- Import `count_stitches_per_color`, `assign_symbols`, `compute_per_color_floss`
- Import `render_pattern_pdf`, `LegendEntry`
- Orchestration:
  1. Validate inputs (existing)
  2. Compute fabric size (existing)
  3. `stitch_counts = count_stitches_per_color(pattern.grid)`
  4. `symbols = assign_symbols(len(palette.colors))`
  5. `floss = compute_per_color_floss(stitch_counts, aida_count, num_strands)`
  6. Build `List[LegendEntry]` from symbols + dmc_colors + floss
  7. Call `render_pattern_pdf(pattern, title, fabric_size, aida_count, margin_cm, legend_entries)`
  8. Return `num_pages=2`

### Step 4: Integration Test Update

**Test:** Update `tests/integration/test_pdf_export_api.py`
- Existing test still passes (200, application/pdf)
- Add test: response PDF has 2 pages

### Step 5: Verify
```bash
pytest -v
pytest --cov=app tests/ -v
black --check app/ tests/
```

## Files Changed/Created

| File | Action |
|------|--------|
| `app/domain/services/floss.py` | MODIFY — add `ColorFlossEstimate`, `compute_per_color_floss()` |
| `app/infrastructure/pdf_export/pdf_generator.py` | MODIFY — refactor to helpers, add `LegendEntry`, `_draw_legend_page()`, `render_pattern_pdf()` |
| `app/application/use_cases/export_pattern_to_pdf.py` | MODIFY — orchestrate legend data, call `render_pattern_pdf()` |
| `tests/unit/test_floss_estimation.py` | MODIFY — add per-color floss tests |
| `tests/unit/test_pdf_legend.py` | CREATE — legend page rendering tests |
| `tests/unit/use_cases/test_export_pattern_to_pdf.py` | MODIFY — update num_pages to 2 |
| `tests/integration/test_pdf_export_api.py` | MODIFY — add 2-page assertion |

## What Does NOT Change
- `symbol_map.py`, `stitch_count.py` — unchanged, just consumed
- `render_overview_page()` — keeps working (refactored internally but same API)
- All existing 84 tests pass without modification (except use case test updating num_pages)
- Domain models, web layer, config — unchanged
