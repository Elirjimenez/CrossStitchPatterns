import pytest
from app.domain.model.pattern import PatternGrid


def test_pattern_grid_validates_dimensions():
    grid = PatternGrid(width=2, height=2, cells=[[0, 1], [1, 0]])
    assert grid.cells[0][1] == 1

    with pytest.raises(ValueError):
        PatternGrid(width=2, height=2, cells=[[0, 1]])  # wrong height

    with pytest.raises(ValueError):
        PatternGrid(width=2, height=2, cells=[[0], [1]])  # wrong width
