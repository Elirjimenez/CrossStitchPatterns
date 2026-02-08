from io import BytesIO

import pypdf

from app.domain.model.pattern import Pattern, PatternGrid, Palette
from app.domain.services.pattern_tiling import compute_tiles
from app.domain.services.symbol_map import assign_symbols
from app.infrastructure.pdf_export.pattern_renderer import render_grid_pages


def _make_pattern(width: int, height: int, num_colors: int = 3) -> Pattern:
    cells = [[c % num_colors for c in range(width)] for _ in range(height)]
    colors = [(i * 80 % 256, i * 50 % 256, i * 120 % 256) for i in range(num_colors)]
    return Pattern(
        grid=PatternGrid(width=width, height=height, cells=cells),
        palette=Palette(colors=colors),
    )


class TestRenderGridPagesBasic:
    def test_returns_valid_pdf_bytes(self):
        pattern = _make_pattern(4, 3)
        symbols = assign_symbols(3)
        tiling = compute_tiles(4, 3, cols_per_page=32, rows_per_page=49)

        result = render_grid_pages(pattern, symbols, tiling.tiles, variant="bw")

        assert isinstance(result, bytes)
        assert result[:5] == b"%PDF-"

    def test_small_pattern_one_page(self):
        pattern = _make_pattern(4, 3)
        symbols = assign_symbols(3)
        tiling = compute_tiles(4, 3, cols_per_page=32, rows_per_page=49)

        result = render_grid_pages(pattern, symbols, tiling.tiles, variant="bw")
        reader = pypdf.PdfReader(BytesIO(result))

        assert len(reader.pages) == 1

    def test_wide_pattern_two_pages(self):
        pattern = _make_pattern(60, 45)
        symbols = assign_symbols(3)
        tiling = compute_tiles(60, 45, cols_per_page=32, rows_per_page=49)

        result = render_grid_pages(pattern, symbols, tiling.tiles, variant="bw")
        reader = pypdf.PdfReader(BytesIO(result))

        assert len(reader.pages) == 2


class TestRenderGridPagesContent:
    def test_bw_page_contains_symbol_text(self):
        pattern = _make_pattern(4, 3)
        symbols = assign_symbols(3)
        tiling = compute_tiles(4, 3, cols_per_page=32, rows_per_page=49)

        result = render_grid_pages(pattern, symbols, tiling.tiles, variant="bw")
        reader = pypdf.PdfReader(BytesIO(result))
        text = reader.pages[0].extract_text()

        # At least one symbol should appear in the extracted text
        found = any(s in text for s in symbols)
        assert found, f"No symbols found in page text: {text!r}"

    def test_page_contains_page_number(self):
        pattern = _make_pattern(60, 45)
        symbols = assign_symbols(3)
        tiling = compute_tiles(60, 45, cols_per_page=32, rows_per_page=49)

        result = render_grid_pages(pattern, symbols, tiling.tiles, variant="bw")
        reader = pypdf.PdfReader(BytesIO(result))
        text = reader.pages[0].extract_text()

        assert "1 / 2" in text

    def test_second_page_has_correct_number(self):
        pattern = _make_pattern(60, 45)
        symbols = assign_symbols(3)
        tiling = compute_tiles(60, 45, cols_per_page=32, rows_per_page=49)

        result = render_grid_pages(pattern, symbols, tiling.tiles, variant="bw")
        reader = pypdf.PdfReader(BytesIO(result))
        text = reader.pages[1].extract_text()

        assert "2 / 2" in text


class TestRenderGridPagesColorVariant:
    def test_color_variant_returns_valid_pdf(self):
        pattern = _make_pattern(4, 3)
        symbols = assign_symbols(3)
        tiling = compute_tiles(4, 3, cols_per_page=32, rows_per_page=49)

        result = render_grid_pages(pattern, symbols, tiling.tiles, variant="color")

        assert isinstance(result, bytes)
        assert result[:5] == b"%PDF-"

    def test_color_variant_contains_symbols(self):
        pattern = _make_pattern(4, 3)
        symbols = assign_symbols(3)
        tiling = compute_tiles(4, 3, cols_per_page=32, rows_per_page=49)

        result = render_grid_pages(pattern, symbols, tiling.tiles, variant="color")
        reader = pypdf.PdfReader(BytesIO(result))
        text = reader.pages[0].extract_text()

        found = any(s in text for s in symbols)
        assert found, f"No symbols found in color page text: {text!r}"


class TestRenderGridPagesStitchNumbers:
    def test_page_contains_stitch_numbers(self):
        pattern = _make_pattern(60, 45)
        symbols = assign_symbols(3)
        tiling = compute_tiles(60, 45, cols_per_page=32, rows_per_page=49)

        result = render_grid_pages(pattern, symbols, tiling.tiles, variant="bw")
        reader = pypdf.PdfReader(BytesIO(result))
        text = reader.pages[0].extract_text()

        # Should have stitch number "10" on first page
        assert "10" in text
