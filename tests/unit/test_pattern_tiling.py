import pytest

from app.domain.services.pattern_tiling import compute_tiles


class TestComputeTilesSmallPattern:
    """A pattern smaller than one page → 1 tile."""

    def test_small_pattern_returns_one_tile(self):
        result = compute_tiles(4, 3, cols_per_page=32, rows_per_page=49)
        assert result.total_pages == 1
        assert len(result.tiles) == 1

    def test_small_pattern_tile_covers_full_grid(self):
        result = compute_tiles(4, 3, cols_per_page=32, rows_per_page=49)
        tile = result.tiles[0]
        assert tile.col_start == 0
        assert tile.col_end == 4
        assert tile.row_start == 0
        assert tile.row_end == 3

    def test_small_pattern_tile_page_index_is_zero(self):
        result = compute_tiles(4, 3, cols_per_page=32, rows_per_page=49)
        assert result.tiles[0].page_index == 0


class TestComputeTilesWidePattern:
    """A 60×45 pattern → 2 tiles (2 cols × 1 row)."""

    def test_wide_pattern_returns_two_tiles(self):
        result = compute_tiles(60, 45, cols_per_page=32, rows_per_page=49)
        assert result.total_pages == 2
        assert len(result.tiles) == 2

    def test_first_tile_spans_full_columns(self):
        result = compute_tiles(60, 45, cols_per_page=32, rows_per_page=49)
        tile = result.tiles[0]
        assert tile.col_start == 0
        assert tile.col_end == 32
        assert tile.row_start == 0
        assert tile.row_end == 45

    def test_second_tile_has_reduced_width(self):
        result = compute_tiles(60, 45, cols_per_page=32, rows_per_page=49)
        tile = result.tiles[1]
        assert tile.col_start == 32
        assert tile.col_end == 60  # 28 columns remaining
        assert tile.row_start == 0
        assert tile.row_end == 45


class TestComputeTilesLargePattern:
    """A 100×100 pattern → multiple tiles."""

    def test_large_pattern_returns_correct_tile_count(self):
        # cols: ceil(100/32) = 4, rows: ceil(100/49) = 3 → 12 tiles
        result = compute_tiles(100, 100, cols_per_page=32, rows_per_page=49)
        assert result.total_pages == 12
        assert len(result.tiles) == 12

    def test_tiles_sorted_row_then_column(self):
        result = compute_tiles(100, 100, cols_per_page=32, rows_per_page=49)
        # First row: tiles 0-3, second row: 4-7, third row: 8-11
        assert result.tiles[0].row_start == 0
        assert result.tiles[0].col_start == 0
        assert result.tiles[1].row_start == 0
        assert result.tiles[1].col_start == 32
        assert result.tiles[4].row_start == 49
        assert result.tiles[4].col_start == 0

    def test_last_tile_has_reduced_dimensions(self):
        result = compute_tiles(100, 100, cols_per_page=32, rows_per_page=49)
        last = result.tiles[-1]
        # Last col: 96..100 (4 cols), last row: 98..100 (2 rows)
        assert last.col_start == 96
        assert last.col_end == 100
        assert last.row_start == 98
        assert last.row_end == 100


class TestComputeTilesExactFit:
    """Pattern that fits exactly in one page."""

    def test_exact_fit_returns_one_tile(self):
        result = compute_tiles(32, 49, cols_per_page=32, rows_per_page=49)
        assert result.total_pages == 1

    def test_one_stitch_over_creates_second_page_column(self):
        result = compute_tiles(33, 49, cols_per_page=32, rows_per_page=49)
        assert result.total_pages == 2

    def test_one_stitch_over_creates_second_page_row(self):
        result = compute_tiles(32, 50, cols_per_page=32, rows_per_page=49)
        assert result.total_pages == 2


class TestCenterLineCalculation:
    """Center lines fall between the two middle rows/columns."""

    def test_even_width_center_col_present(self):
        # 60-wide: center at 30.0, between cols 29 and 30
        result = compute_tiles(60, 45, cols_per_page=32, rows_per_page=49)
        # Tile 0 covers cols 0..32: center 30.0 is within → local = 30.0
        assert result.tiles[0].center_col == pytest.approx(30.0)
        # Tile 1 covers cols 32..60: center 30.0 is NOT within
        assert result.tiles[1].center_col is None

    def test_even_height_center_row_present(self):
        # 45 rows → center at 22.5
        result = compute_tiles(60, 45, cols_per_page=32, rows_per_page=49)
        # Both tiles cover rows 0..45 → center_row = 22.5
        assert result.tiles[0].center_row == pytest.approx(22.5)
        assert result.tiles[1].center_row == pytest.approx(22.5)

    def test_odd_dimension_center(self):
        # 5-wide: center at 2.5
        result = compute_tiles(5, 5, cols_per_page=32, rows_per_page=49)
        assert result.tiles[0].center_col == pytest.approx(2.5)
        assert result.tiles[0].center_row == pytest.approx(2.5)

    def test_center_on_second_tile(self):
        # 100-wide: center at 50.0, tile 0: 0..32, tile 1: 32..64 contains it
        result = compute_tiles(100, 10, cols_per_page=32, rows_per_page=49)
        assert result.tiles[0].center_col is None  # 50 not in 0..32
        assert result.tiles[1].center_col == pytest.approx(50.0 - 32)  # local = 18.0


class TestTilingResultMetadata:
    def test_result_contains_per_page_constants(self):
        result = compute_tiles(60, 45, cols_per_page=32, rows_per_page=49)
        assert result.cols_per_page == 32
        assert result.rows_per_page == 49


class TestComputeTilesInvalidInputs:
    def test_zero_width_raises(self):
        with pytest.raises(ValueError):
            compute_tiles(0, 10, cols_per_page=32, rows_per_page=49)

    def test_zero_height_raises(self):
        with pytest.raises(ValueError):
            compute_tiles(10, 0, cols_per_page=32, rows_per_page=49)

    def test_zero_cols_per_page_raises(self):
        with pytest.raises(ValueError):
            compute_tiles(10, 10, cols_per_page=0, rows_per_page=49)

    def test_zero_rows_per_page_raises(self):
        with pytest.raises(ValueError):
            compute_tiles(10, 10, cols_per_page=32, rows_per_page=0)

    def test_negative_dimensions_raise(self):
        with pytest.raises(ValueError):
            compute_tiles(-5, 10, cols_per_page=32, rows_per_page=49)
