import pytest
from app.domain.data.dmc_colors import DMC_COLORS
from app.domain.services.color_matching import (
    delta_e,
    find_nearest_dmc,
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
