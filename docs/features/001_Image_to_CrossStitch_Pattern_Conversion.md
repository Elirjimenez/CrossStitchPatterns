# Plan: Phase 2 — Image to Cross-Stitch Pattern Conversion

## Context
The core feature of the app: convert an image into a cross-stitch `Pattern` with colors matched to **real DMC thread colors** (447 colors). Color matching uses **CIE LAB color space** for perceptual accuracy. The DMC color database is stored as a Python dict in the domain layer (no new dependencies).

**Branch:** `feature/image-to-pattern` (already created)

## Architecture Overview

```
Image bytes → [Infrastructure: Pillow adapter] → resized pixel grid (List[List[RGB]])
    → [Domain: DMC color matching in LAB space] → Pattern (grid + DMC palette)
```

- **Domain layer** (pure Python, no deps): DMC database, RGB→LAB conversion, nearest-DMC matching, pattern building
- **Infrastructure layer** (Pillow): image loading, resizing, pixel extraction
- **Application layer**: `ConvertImageToPattern` use case orchestrating both
- **Web layer**: `POST /api/patterns/convert` endpoint

## Implementation Order (TDD)

### Step 1: DMC Color Database
**Test:** `tests/unit/test_dmc_colors.py`
- `DMC_COLORS` dict has 447 entries
- Each entry: `dmc_number (str) → (name: str, r: int, g: int, b: int)`
- Spot-check known values (e.g., DMC 310 = Black = (0,0,0), DMC B5200 = White)

**Implement:** `app/domain/data/dmc_colors.py`
- Python dict with all 447 DMC colors scraped from the reference site
- Frozen dataclass `DmcColor(number: str, name: str, r: int, g: int, b: int)`

### Step 2: RGB→LAB Conversion (pure Python)
**Test:** `tests/unit/test_color_matching.py` (first batch)
- `rgb_to_lab((255, 0, 0))` returns known LAB values for red
- `rgb_to_lab((0, 0, 0))` returns (0, 0, 0) for black
- `rgb_to_lab((255, 255, 255))` returns L≈100 for white

**Implement:** `app/domain/services/color_matching.py`
- `rgb_to_lab(rgb: RGB) -> Tuple[float, float, float]`
- Uses standard sRGB→XYZ→LAB formulas (~15 lines of `math` module code)

### Step 3: Nearest DMC Color Matching
**Test:** `tests/unit/test_color_matching.py` (second batch)
- `find_nearest_dmc((0, 0, 0))` returns DMC 310 (Black)
- `find_nearest_dmc((255, 255, 255))` returns DMC B5200 or White
- `find_nearest_dmc((255, 0, 0))` returns a red DMC color
- `delta_e(lab1, lab2)` returns 0 for identical colors, >0 for different

**Implement:** `app/domain/services/color_matching.py` (extend)
- `delta_e(lab1, lab2) -> float` — CIE76 Euclidean distance in LAB
- `find_nearest_dmc(rgb: RGB) -> DmcColor` — converts to LAB, compares against all 447
- Pre-compute LAB values for all 447 DMC colors (cached on first use)

### Step 4: Palette Selection (Top N DMC Colors)
**Test:** `tests/unit/test_color_matching.py` (third batch)
- `select_palette(pixels, num_colors=8)` returns a `Palette` with ≤8 DMC colors
- All returned colors are valid DMC colors
- Most frequent matched colors are selected

**Implement:** `app/domain/services/color_matching.py` (extend)
- `map_pixels_to_dmc(pixels: List[RGB]) -> List[DmcColor]` — map each pixel to nearest DMC
- `select_palette(pixels: List[RGB], num_colors: int) -> Tuple[Palette, List[List[int]]]`
  - Map all pixels to DMC, count frequencies, pick top N
  - Remap pixels that matched non-selected DMC colors to nearest selected one
  - Return `Palette` (the N DMC RGB values) + 2D grid of palette indices

### Step 5: Image Loading Infrastructure Adapter
**Test:** `tests/unit/test_image_adapter.py`
- `load_and_resize(image_bytes, target_w, target_h)` returns `List[List[RGB]]`
- Rejects invalid image data
- Rejects oversized dimensions (use `max_pattern_size` from config)

**Implement:** `app/infrastructure/image_processing/image_converter.py`
- `load_and_resize(image_bytes: bytes, width: int, height: int) -> List[List[RGB]]`
- Uses Pillow: `Image.open(BytesIO(data)).convert("RGB").resize((w, h))`
- Extracts pixel grid as `List[List[RGB]]`

### Step 6: ConvertImageToPattern Use Case
**Test:** `tests/unit/use_cases/test_convert_image_to_pattern.py`
- Provide a tiny synthetic image (e.g., 2x2 pixels), verify it returns a valid `Pattern`
- Pattern grid dimensions match request
- Palette colors are all valid DMC RGB values

**Implement:** `app/application/use_cases/convert_image_to_pattern.py`
- Request: `ConvertImageRequest(image_data: bytes, target_width: int, target_height: int, num_colors: int)`
- Result: `ConvertImageResult(pattern: Pattern, dmc_colors: List[DmcColor])`
- Orchestrates: image adapter → pixel grid → select_palette → build Pattern

### Step 7: API Endpoint
**Test:** `tests/integration/test_image_conversion_api.py`
- `POST /api/patterns/convert` with multipart image upload returns 200
- Response contains grid, palette, and DMC color info
- Invalid file returns appropriate error

**Implement:** `app/web/api/routes/patterns.py` (add to existing router)
- `POST /api/patterns/convert` with `UploadFile`
- Parameters: `target_width`, `target_height`, `num_colors`
- Returns pattern JSON with DMC color details

### Step 8: Verify
```bash
pytest -v                           # All tests pass
pytest --cov=app tests/ -v          # Coverage stays ≥80%
black --check app/ tests/           # Formatting OK
```

## Files Changed/Created

| File | Action |
|------|--------|
| `app/domain/data/__init__.py` | CREATE — empty |
| `app/domain/data/dmc_colors.py` | CREATE — 447-entry DMC color dict + `DmcColor` dataclass |
| `app/domain/services/color_matching.py` | CREATE — `rgb_to_lab`, `delta_e`, `find_nearest_dmc`, `select_palette` |
| `app/infrastructure/image_processing/image_converter.py` | MODIFY — `load_and_resize()` with Pillow |
| `app/application/use_cases/convert_image_to_pattern.py` | MODIFY — full use case implementation |
| `app/web/api/routes/patterns.py` | MODIFY — add `/convert` endpoint |
| `tests/unit/test_dmc_colors.py` | CREATE |
| `tests/unit/test_color_matching.py` | CREATE |
| `tests/unit/test_image_adapter.py` | CREATE |
| `tests/unit/use_cases/test_convert_image_to_pattern.py` | CREATE |
| `tests/integration/test_image_conversion_api.py` | MODIFY (exists but empty) |

## Key Design Decisions

1. **LAB color space** (CIE76 Delta E) for perceptual color matching — pure Python, no new deps
2. **DMC database as Python dict** in domain layer — no file I/O, versioned with code
3. **447 real DMC colors** — user gets actual thread numbers they can buy
4. **No new dependencies** — RGB→LAB is ~15 lines of math, Pillow handles image I/O
5. **Domain stays pure** — color matching logic has zero framework dependencies

## What Does NOT Change
- Existing 24 tests stay untouched
- `fabric.py`, `floss.py` — unchanged
- `config.py`, `exceptions.py`, `logging.py` — unchanged
- `health.py` — unchanged
