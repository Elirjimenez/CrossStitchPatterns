# Plan: PDF Export — Feature 1: Overview Page

## Context

The user wants printable cross-stitch pattern PDFs in two variants (Color and B/W). This is a large feature being split into **3 incremental features**:

1. **Feature 1 (this plan): Overview Page** — PDF infrastructure + overview page + API endpoint
2. **Feature 2: Legend Page** — DMC floss list table with per-color stitch counts and skeins
3. **Feature 3: Pattern Grid Pages** — Multi-page grid with symbols, thick lines every 10 stitches, page numbers

Each feature is a separate branch, merged before the next starts. Feature 1 establishes shared infrastructure used by all three.

**Pre-requisite:** Merge `feature/image-to-pattern` into `main` before creating the new branch.

**Branch:** `feature/pdf-overview-page`

## Architecture

```
Domain (pure Python):
  symbol_map.py      → assign symbols to palette indices
  stitch_count.py    → count stitches per color in a grid

Application:
  export_pattern_to_pdf.py → ExportPdfRequest/Result, orchestrates domain + infra

Infrastructure (ReportLab):
  pdf_generator.py   → render_overview_page() using Canvas

Web:
  patterns.py        → POST /api/patterns/export-pdf
```

## Implementation Steps (TDD)

### Step 1: Domain — Symbol Map
**Test:** `tests/unit/test_symbol_map.py`
- `assign_symbols(5)` returns 5 unique single-character strings
- `assign_symbols(1)` works for single color
- `assign_symbols(40)` works (max capacity)
- `assign_symbols(0)` raises DomainException
- `assign_symbols(50)` raises DomainException (exceeds available symbols)

**Implement:** `app/domain/services/symbol_map.py`
- `SYMBOLS`: list of ~40 distinguishable ASCII characters (used in Courier font)
  ```
  @, #, $, %, &, *, +, =, ~, ?, !, ^, <, >, /, \, |,
  A, B, C, D, E, F, G, H, I, J, K, L, M, N, O, P, Q, R, S, T, U, V, W, X, Y, Z
  ```
- `assign_symbols(num_colors: int) -> List[str]` — returns first N symbols from the list

### Step 2: Domain — Stitch Counting
**Test:** `tests/unit/test_stitch_count.py`
- 2x2 grid `[[0,1],[1,0]]` → index 0: 2 stitches, index 1: 2 stitches
- All same index → single entry with count = width * height
- Results sorted by palette_index

**Implement:** `app/domain/services/stitch_count.py`
```python
@dataclass(frozen=True)
class ColorStitchCount:
    palette_index: int
    count: int

def count_stitches_per_color(grid: PatternGrid) -> List[ColorStitchCount]
```

### Step 3: Infrastructure — Overview Page Renderer
**Test:** `tests/unit/test_pdf_overview.py`
- `render_overview_page()` produces bytes starting with `%PDF`
- PDF contains the title text
- PDF contains stitch dimensions (e.g., "120 x 90 stitches")
- PDF contains fabric size info
- PDF is exactly 1 page

**Implement:** `app/infrastructure/pdf_export/pdf_generator.py`
```python
def render_overview_page(
    pattern: Pattern,
    title: str,
    fabric_size: FabricSize,
    aida_count: int,
    margin_cm: float,
) -> bytes
```

Rendering logic (A4 page, ReportLab Canvas):
1. **Title** — Helvetica-Bold 24pt, centered at top
2. **Pattern thumbnail** — fill available area preserving aspect ratio, draw colored rectangles (one per stitch, scaled down)
3. **Footer line 1** — "120 x 90 stitches" centered
4. **Footer line 2** — "Fabric: 31.8 x 26.3 cm (14ct Aida, 5.0 cm margin)" centered

### Step 4: Use Case — ExportPatternToPdf
**Test:** `tests/unit/use_cases/test_export_pattern_to_pdf.py`
- `execute()` returns `ExportPdfResult` with non-empty `pdf_bytes`
- Result has `variant` matching request
- Result has `num_pages == 1` (overview only for now)
- Rejects empty title
- Rejects invalid variant (not "color" / "bw")

**Implement:** `app/application/use_cases/export_pattern_to_pdf.py`
```python
@dataclass(frozen=True)
class ExportPdfRequest:
    pattern: Pattern
    dmc_colors: List[DmcColor]
    title: str
    aida_count: int
    num_strands: int = 2
    margin_cm: float = 5.0
    variant: str = "color"  # "color" or "bw"

@dataclass(frozen=True)
class ExportPdfResult:
    pdf_bytes: bytes
    num_pages: int
    variant: str

class ExportPatternToPdf:
    def execute(self, request: ExportPdfRequest) -> ExportPdfResult
```

Orchestration: validate inputs → compute fabric size → call `render_overview_page()` → return result.

### Step 5: API Endpoint
**Test:** `tests/integration/test_pdf_export_api.py`
- `POST /api/patterns/export-pdf` returns 200 with `application/pdf` content type
- Invalid input returns 422

**Implement:** Add to `app/web/api/routes/patterns.py`
```
POST /api/patterns/export-pdf
Body (JSON): grid, palette, dmc_colors, title, aida_count, num_strands, margin_cm, variant
Response: StreamingResponse with application/pdf
```

### Step 6: Verify
```bash
pytest -v
pytest --cov=app tests/ -v          # Coverage ≥80%
black --check app/ tests/
```

## Files Changed/Created

| File | Action |
|------|--------|
| `app/domain/services/symbol_map.py` | CREATE |
| `app/domain/services/stitch_count.py` | CREATE |
| `app/infrastructure/pdf_export/pdf_generator.py` | POPULATE (currently empty stub) |
| `app/application/use_cases/export_pattern_to_pdf.py` | POPULATE (currently empty stub) |
| `app/web/api/routes/patterns.py` | MODIFY — add `/export-pdf` endpoint |
| `tests/unit/test_symbol_map.py` | CREATE |
| `tests/unit/test_stitch_count.py` | CREATE |
| `tests/unit/test_pdf_overview.py` | CREATE |
| `tests/unit/use_cases/test_export_pattern_to_pdf.py` | CREATE |
| `tests/integration/test_pdf_export_api.py` | CREATE |

## Key Design Decisions

1. **One PDF per variant** — color and B/W are separate PDFs (same structure, grid rendering differs)
2. **Symbol assignment is domain logic** — pure Python, no ReportLab dependency
3. **Stitch counting is domain logic** — reusable by legend (Feature 2) and floss calculations
4. **ASCII symbols in Courier font** — renders well in ReportLab, distinguishable in both color and B/W
5. **No new dependencies** — ReportLab 4.0.9 already in requirements.txt
6. **Canvas-based rendering** — direct canvas operations for full layout control

## Roadmap: Features 2 & 3

### Feature 2: Legend Page (`feature/pdf-legend-page`)
- Add `compute_per_color_floss()` to `app/domain/services/floss.py`
- Add `render_legend_page()` to `pdf_generator.py`
- Update use case to append legend after overview
- PDF grows to 2 pages (overview + legend)

### Feature 3: Pattern Grid Pages (`feature/pdf-pattern-pages`)
- Create `app/domain/services/page_layout.py` — grid tiling logic (split large patterns into pages)
- Add `contrast_color()` to `symbol_map.py` — white text on dark, black text on light
- Add `render_pattern_pages()` to `pdf_generator.py` — color or B/W grid with symbols
- Thick lines every 10 stitches, stitch numbers on edges, "1/14" page numbering
- Update use case for full PDF assembly

## What Does NOT Change
- Existing 56 tests stay untouched
- `color_matching.py`, `dmc_colors.py`, `image_converter.py` — unchanged
- `fabric.py`, `floss.py` — unchanged (until Feature 2)
- `config.py`, `exceptions.py`, `logging.py`, `health.py`, `main.py` — unchanged
