from app.domain.services.confetti import reduce_confetti


class TestReduceConfettiNoChange:
    def test_uniform_grid_unchanged(self):
        cells = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        result = reduce_confetti(cells)
        assert result == cells

    def test_two_color_blocks_unchanged(self):
        """Two solid color blocks should not be altered."""
        cells = [
            [0, 0, 1, 1],
            [0, 0, 1, 1],
            [0, 0, 1, 1],
        ]
        result = reduce_confetti(cells)
        assert result == cells


class TestReduceConfettiSmooths:
    def test_single_isolated_pixel_replaced(self):
        """A single pixel surrounded by a different color gets replaced."""
        cells = [
            [0, 0, 0],
            [0, 1, 0],
            [0, 0, 0],
        ]
        result = reduce_confetti(cells)
        assert result[1][1] == 0

    def test_corner_pixel_not_replaced_if_few_neighbors(self):
        """Corner has only 3 neighbors; threshold requires >= 5 agreeing."""
        cells = [
            [1, 0],
            [0, 0],
        ]
        result = reduce_confetti(cells)
        # Corner (0,0) has only 3 neighbors; not enough for threshold
        assert result[0][0] == 1

    def test_edge_pixel_replaced_if_enough_neighbors(self):
        """Edge pixel with 5 agreeing neighbors should be replaced."""
        cells = [
            [0, 0, 0],
            [1, 0, 0],
            [0, 0, 0],
        ]
        result = reduce_confetti(cells)
        assert result[1][0] == 0

    def test_preserves_edges_between_regions(self):
        """Pixels on a color boundary should not be smoothed away."""
        cells = [
            [0, 0, 0, 1, 1],
            [0, 0, 0, 1, 1],
            [0, 0, 0, 1, 1],
        ]
        result = reduce_confetti(cells)
        assert result == cells


class TestReduceConfettiMultipleColors:
    def test_replaces_with_most_common_neighbor(self):
        """Isolated pixel should become the most common neighbor color."""
        cells = [
            [2, 2, 2],
            [2, 1, 2],
            [2, 2, 2],
        ]
        result = reduce_confetti(cells)
        assert result[1][1] == 2

    def test_multiple_passes_clean_more(self):
        """Multiple passes should clean up cascading confetti."""
        cells = [
            [0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0],
            [0, 0, 1, 0, 0],
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
        ]
        result = reduce_confetti(cells, num_passes=2)
        # Both isolated pixels should be cleaned
        assert result[1][1] == 0
        assert result[2][2] == 0


class TestReduceConfettiReturnsNewList:
    def test_does_not_mutate_input(self):
        cells = [[0, 0, 0], [0, 1, 0], [0, 0, 0]]
        original = [row[:] for row in cells]
        reduce_confetti(cells)
        assert cells == original
