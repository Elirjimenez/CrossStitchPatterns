from __future__ import annotations

from collections import Counter
from typing import List


def reduce_confetti(cells: List[List[int]], num_passes: int = 2) -> List[List[int]]:
    """Replace isolated stitches with the most common neighbor color (mode filter).

    A cell is replaced when at least 5 of its 8-connected neighbors share
    the same color and that color differs from the cell's current color.
    Cells with fewer than 3 neighbors (impossible on any grid >= 2x2,
    but guarded) are left untouched.
    """
    rows = len(cells)
    cols = len(cells[0]) if rows else 0

    for _ in range(num_passes):
        new_cells = [row[:] for row in cells]
        for r in range(rows):
            for c in range(cols):
                neighbors: List[int] = []
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < rows and 0 <= nc < cols:
                            neighbors.append(cells[nr][nc])

                if len(neighbors) < 3:
                    continue

                counter = Counter(neighbors)
                mode_color, mode_count = counter.most_common(1)[0]
                if cells[r][c] != mode_color and mode_count >= 5:
                    new_cells[r][c] = mode_color

        cells = new_cells

    return cells
