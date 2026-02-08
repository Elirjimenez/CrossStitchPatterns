from app.domain.model.pattern import PatternGrid
from app.domain.services.stitch_count import count_stitches_per_color, ColorStitchCount


def test_mixed_grid_counts():
    """2x2 grid with two colors: each appears twice."""
    grid = PatternGrid(width=2, height=2, cells=[[0, 1], [1, 0]])
    result = count_stitches_per_color(grid)

    assert result == [
        ColorStitchCount(palette_index=0, count=2),
        ColorStitchCount(palette_index=1, count=2),
    ]


def test_all_same_color():
    """3x3 grid all index 0 → single entry with count 9."""
    grid = PatternGrid(width=3, height=3, cells=[[0, 0, 0]] * 3)
    result = count_stitches_per_color(grid)

    assert result == [ColorStitchCount(palette_index=0, count=9)]


def test_results_sorted_by_palette_index():
    """Results must be sorted by palette_index ascending."""
    grid = PatternGrid(width=3, height=1, cells=[[2, 0, 1]])
    result = count_stitches_per_color(grid)

    indices = [r.palette_index for r in result]
    assert indices == [0, 1, 2]


def test_single_cell_grid():
    grid = PatternGrid(width=1, height=1, cells=[[0]])
    result = count_stitches_per_color(grid)

    assert result == [ColorStitchCount(palette_index=0, count=1)]


def test_multiple_colors_various_counts():
    grid = PatternGrid(
        width=4,
        height=2,
        cells=[
            [0, 1, 2, 3],
            [0, 0, 1, 3],
        ],
    )
    result = count_stitches_per_color(grid)

    assert result == [
        ColorStitchCount(palette_index=0, count=3),
        ColorStitchCount(palette_index=1, count=2),
        ColorStitchCount(palette_index=2, count=1),
        ColorStitchCount(palette_index=3, count=2),
    ]
