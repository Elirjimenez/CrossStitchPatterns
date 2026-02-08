from collections import Counter
from dataclasses import dataclass
from typing import List

from app.domain.model.pattern import PatternGrid


@dataclass(frozen=True)
class ColorStitchCount:
    palette_index: int
    count: int


def count_stitches_per_color(grid: PatternGrid) -> List[ColorStitchCount]:
    counter: Counter[int] = Counter()
    for row in grid.cells:
        for index in row:
            counter[index] += 1

    return [ColorStitchCount(palette_index=idx, count=cnt) for idx, cnt in sorted(counter.items())]
