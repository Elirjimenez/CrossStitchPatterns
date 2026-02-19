import pytest
from app.domain.data.dmc_colors import DMC_COLORS
from app.domain.services.color_matching import (
    delta_e,
    find_nearest_dmc,
    find_nearest_dmc_batch,
    rgb_to_lab,
    select_palette,
)


class TestRgbToLab:
    def test_black(self):
        L, a, b = rgb_to_lab((0, 0, 0))
        assert L == pytest.approx(0.0, abs=0.5)
        assert a == pytest.approx(0.0, abs=0.5)
        assert b == pytest.approx(0.0, abs=0.5)

    def test_white(self):
        L, a, b = rgb_to_lab((255, 255, 255))
        assert L == pytest.approx(100.0, abs=0.5)
        assert a == pytest.approx(0.0, abs=0.5)
        assert b == pytest.approx(0.0, abs=0.5)

    def test_red(self):
        L, a, b = rgb_to_lab((255, 0, 0))
        # Known CIE LAB values for pure red
        assert L == pytest.approx(53.23, abs=1.0)
        assert a == pytest.approx(80.11, abs=1.0)
        assert b == pytest.approx(67.22, abs=1.0)

    def test_green(self):
        L, a, b = rgb_to_lab((0, 128, 0))
        # Green should have negative a (green axis)
        assert a < 0

    def test_blue(self):
        L, a, b = rgb_to_lab((0, 0, 255))
        # Blue should have negative b (blue axis)
        assert b < 0


class TestDeltaE:
    def test_identical_colors(self):
        lab = rgb_to_lab((128, 64, 32))
        assert delta_e(lab, lab) == pytest.approx(0.0)

    def test_different_colors(self):
        lab1 = rgb_to_lab((255, 0, 0))
        lab2 = rgb_to_lab((0, 0, 255))
        assert delta_e(lab1, lab2) > 0


class TestFindNearestDmc:
    def test_black_matches_dmc_310(self):
        dmc = find_nearest_dmc((0, 0, 0))
        assert dmc.number == "310"
        assert dmc.name == "Black"

    def test_pure_white_matches_snow_white(self):
        dmc = find_nearest_dmc((255, 255, 255))
        assert dmc.number == "B5200"

    def test_red_returns_red_family(self):
        dmc = find_nearest_dmc((255, 0, 0))
        # Should match some red DMC color
        assert dmc.r > 150
        assert dmc.g < 80
        assert dmc.b < 80


class TestSelectPalette:
    def test_returns_correct_number_of_colors(self):
        # 2x2 grid: black, white, red, blue
        pixels = [
            [(0, 0, 0), (255, 255, 255)],
            [(255, 0, 0), (0, 0, 255)],
        ]
        palette, grid, dmc_list = select_palette(pixels, num_colors=4)
        assert len(palette.colors) <= 4
        assert len(dmc_list) == len(palette.colors)

    def test_grid_dimensions_match_input(self):
        pixels = [
            [(0, 0, 0), (255, 255, 255)],
            [(255, 0, 0), (0, 0, 255)],
        ]
        palette, grid, dmc_list = select_palette(pixels, num_colors=4)
        assert len(grid) == 2  # height
        assert len(grid[0]) == 2  # width

    def test_grid_indices_valid(self):
        pixels = [
            [(0, 0, 0), (255, 255, 255)],
            [(255, 0, 0), (0, 0, 255)],
        ]
        palette, grid, dmc_list = select_palette(pixels, num_colors=4)
        num_colors = len(palette.colors)
        for row in grid:
            for idx in row:
                assert 0 <= idx < num_colors

    def test_palette_colors_are_dmc(self):
        pixels = [
            [(0, 0, 0), (255, 255, 255)],
            [(128, 0, 0), (0, 128, 0)],
        ]
        palette, grid, dmc_list = select_palette(pixels, num_colors=4)
        dmc_rgb_set = {(c.r, c.g, c.b) for c in DMC_COLORS.values()}
        for color in palette.colors:
            assert color in dmc_rgb_set

    def test_limits_to_num_colors(self):
        # 3x1 grid with 3 very different colors, request only 2
        pixels = [[(0, 0, 0), (255, 255, 255), (255, 0, 0)]]
        palette, grid, dmc_list = select_palette(pixels, num_colors=2)
        assert len(palette.colors) == 2
        assert len(dmc_list) == 2


class TestFindNearestDmcBatch:
    """Tests for the vectorised batch DMC matcher."""

    def test_single_pixel_matches_scalar_function(self):
        # Batch result for one pixel must agree with the scalar find_nearest_dmc
        import numpy as np
        for rgb in [(0, 0, 0), (255, 255, 255), (255, 0, 0), (0, 0, 255)]:
            scalar = find_nearest_dmc(rgb)
            arr = np.array([rgb], dtype=np.uint8)
            batch_idx = find_nearest_dmc_batch(arr)
            dmc_list = list(DMC_COLORS.values())
            batch_color = dmc_list[batch_idx[0]]
            assert batch_color.number == scalar.number, (
                f"Mismatch for {rgb}: scalar={scalar.number}, batch={batch_color.number}"
            )

    def test_batch_multiple_pixels(self):
        import numpy as np
        rgbs = [(0, 0, 0), (255, 255, 255), (255, 0, 0), (0, 128, 0), (0, 0, 255)]
        arr = np.array(rgbs, dtype=np.uint8)
        indices = find_nearest_dmc_batch(arr)
        assert indices.shape == (len(rgbs),)
        dmc_list = list(DMC_COLORS.values())
        for i, rgb in enumerate(rgbs):
            expected = find_nearest_dmc(rgb)
            got = dmc_list[indices[i]]
            assert got.number == expected.number

    def test_batch_handles_single_row_image(self):
        # select_palette must give same result whether grid is tiny or large
        pixels = [[(0, 0, 0), (255, 255, 255)], [(255, 0, 0), (0, 0, 255)]]
        palette, grid, dmc_list = select_palette(pixels, num_colors=4)
        assert len(grid) == 2
        assert len(grid[0]) == 2
        assert all(0 <= idx < len(palette.colors) for row in grid for idx in row)

    def test_select_palette_fast_on_large_grid(self):
        # A 100x100 grid (10 000 pixels) should complete in under 5 seconds
        import time
        row = [(r, g, b) for r in range(0, 256, 26) for g in range(0, 256, 26) for b in (0, 128, 255)]
        # Trim/extend to 100 wide
        row = (row * 4)[:100]
        pixels = [row] * 100
        t0 = time.perf_counter()
        palette, grid, dmc_list = select_palette(pixels, num_colors=10)
        elapsed = time.perf_counter() - t0
        assert elapsed < 5.0, f"select_palette took {elapsed:.2f}s on 100x100 grid — too slow"


class TestSelectPaletteFrequencyThreshold:
    def test_threshold_excludes_rare_color(self):
        # 9 black pixels + 1 red pixel → red is 10% of total
        # With threshold=15%, red should be filtered out → only 1 color survives
        pixels = [[(0, 0, 0)] * 9 + [(255, 0, 0)]]
        palette, grid, dmc_list = select_palette(pixels, num_colors=10, min_frequency_pct=15.0)
        assert len(palette.colors) == 1
        assert len(dmc_list) == 1
        # All grid indices must be valid
        for idx in grid[0]:
            assert 0 <= idx < len(palette.colors)

    def test_threshold_zero_disables_filtering(self):
        # With threshold=0.0, even a 1-pixel color is kept (up to num_colors)
        pixels = [[(0, 0, 0)] * 9 + [(255, 0, 0)]]
        palette, grid, dmc_list = select_palette(pixels, num_colors=10, min_frequency_pct=0.0)
        assert len(palette.colors) >= 2

    def test_threshold_and_num_colors_both_apply(self):
        # 5 black, 3 white, 1 red, 1 blue — threshold 15% removes red and blue
        # Then num_colors=1 caps to just black
        pixels = [[(0, 0, 0)] * 5 + [(255, 255, 255)] * 3 + [(255, 0, 0)] + [(0, 0, 255)]]
        palette, grid, dmc_list = select_palette(pixels, num_colors=1, min_frequency_pct=15.0)
        assert len(palette.colors) == 1

    def test_default_threshold_filters_jpeg_artifacts(self):
        # Simulates a simple image: dominant red + many tiny variations (each 1 pixel)
        # in a 100-pixel row. Each artifact is < 1% of total pixels.
        dominant = (220, 20, 30)  # vivid red
        # 91 dominant pixels + 9 slightly different "artifact" colors (1 each)
        artifacts = [
            (221, 21, 31), (219, 19, 29), (222, 22, 32),
            (218, 18, 28), (223, 23, 33), (217, 17, 27),
            (224, 24, 34), (216, 16, 26), (225, 25, 35),
        ]
        row = [dominant] * 91 + artifacts
        pixels = [row]
        # Use 1.5% threshold to ensure artifacts (1/100 = 1% each) are filtered
        palette, grid, dmc_list = select_palette(pixels, num_colors=10, min_frequency_pct=1.5)
        # Only the dominant red DMC color should survive
        assert len(palette.colors) == 1
