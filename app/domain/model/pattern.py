from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple

RGB = Tuple[int, int, int]

@dataclass(frozen=True)
class PatternGrid:
    """A 2D grid of palette indices."""
    width: int
    height: int
    cells: List[List[int]]  # cells[y][x] -> palette index

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("width/height must be > 0")
        if len(self.cells) != self.height:
            raise ValueError("cells height mismatch")
        for row in self.cells:
            if len(row) != self.width:
                raise ValueError("cells width mismatch")

@dataclass(frozen=True)
class Palette:
    colors: List[RGB]  # index -> RGB

    def __post_init__(self) -> None:
        if not self.colors:
            raise ValueError("palette must not be empty")

@dataclass(frozen=True)
class Pattern:
    grid: PatternGrid
    palette: Palette
