import pytest
from app.domain.services.floss import compute_floss_estimate, compute_per_color_floss
from app.domain.services.stitch_count import ColorStitchCount


def test_floss_estimate_14ct_2_strands():
    """14ct Aida, 2 strands: ~1714 stitches per skein before margin."""
    result = compute_floss_estimate(
        total_stitches=14000,
        num_colors=8,
        aida_count=14,
        num_strands=2,
    )

    assert result.total_stitches == 14000
    assert result.num_colors == 8
    assert result.skeins_per_color == 2
    assert result.total_skeins == 16


def test_floss_estimate_14ct_3_strands():
    """14ct Aida, 3 strands: uses more thread, needs more skeins."""
    result_2 = compute_floss_estimate(
        total_stitches=14000,
        num_colors=4,
        aida_count=14,
        num_strands=2,
    )
    result_3 = compute_floss_estimate(
        total_stitches=14000,
        num_colors=4,
        aida_count=14,
        num_strands=3,
    )

    # 3 strands consumes more thread per stitch than 2
    assert result_3.skeins_per_color > result_2.skeins_per_color
    assert result_3.total_skeins > result_2.total_skeins


def test_floss_estimate_higher_aida_uses_less_thread():
    """18ct Aida has smaller stitches, so less thread per stitch."""
    result_14ct = compute_floss_estimate(
        total_stitches=14000,
        num_colors=8,
        aida_count=14,
        num_strands=2,
    )
    result_18ct = compute_floss_estimate(
        total_stitches=14000,
        num_colors=8,
        aida_count=18,
        num_strands=2,
    )

    assert result_18ct.total_skeins < result_14ct.total_skeins


def test_floss_estimate_default_strands_is_2():
    """Default num_strands should be 2 (most common for cross-stitch)."""
    result = compute_floss_estimate(
        total_stitches=14000,
        num_colors=8,
        aida_count=14,
    )
    explicit = compute_floss_estimate(
        total_stitches=14000,
        num_colors=8,
        aida_count=14,
        num_strands=2,
    )

    assert result.total_skeins == explicit.total_skeins


def test_floss_estimate_rejects_invalid_inputs():
    with pytest.raises(ValueError):
        compute_floss_estimate(total_stitches=0, num_colors=8, aida_count=14)
    with pytest.raises(ValueError):
        compute_floss_estimate(total_stitches=14000, num_colors=0, aida_count=14)
    with pytest.raises(ValueError):
        compute_floss_estimate(total_stitches=14000, num_colors=8, aida_count=0)
    with pytest.raises(ValueError):
        compute_floss_estimate(total_stitches=14000, num_colors=8, aida_count=14, num_strands=0)
    with pytest.raises(ValueError):
        compute_floss_estimate(total_stitches=14000, num_colors=8, aida_count=14, num_strands=7)
    with pytest.raises(ValueError):
        compute_floss_estimate(total_stitches=14000, num_colors=8, aida_count=14, margin_ratio=-0.1)


# --- Per-color floss estimation tests ---


def test_per_color_floss_two_colors():
    """Two colors with different stitch counts yield different skein counts."""
    counts = [
        ColorStitchCount(palette_index=0, count=500),
        ColorStitchCount(palette_index=1, count=3000),
    ]
    result = compute_per_color_floss(counts, aida_count=14)

    assert len(result) == 2
    assert result[0].palette_index == 0
    assert result[0].stitch_count == 500
    assert result[1].palette_index == 1
    assert result[1].stitch_count == 3000
    # More stitches → more skeins
    assert result[1].skeins >= result[0].skeins


def test_per_color_floss_sorted_by_palette_index():
    """Results are sorted by palette_index even if input is not."""
    counts = [
        ColorStitchCount(palette_index=2, count=100),
        ColorStitchCount(palette_index=0, count=200),
        ColorStitchCount(palette_index=1, count=150),
    ]
    result = compute_per_color_floss(counts, aida_count=14)

    assert [r.palette_index for r in result] == [0, 1, 2]


def test_per_color_floss_minimum_one_skein():
    """Even a single stitch requires at least 1 skein."""
    counts = [ColorStitchCount(palette_index=0, count=1)]
    result = compute_per_color_floss(counts, aida_count=14)

    assert result[0].skeins >= 1


def test_per_color_floss_rejects_invalid_aida():
    with pytest.raises(ValueError):
        compute_per_color_floss([ColorStitchCount(palette_index=0, count=100)], aida_count=0)


def test_per_color_floss_rejects_invalid_strands():
    with pytest.raises(ValueError):
        compute_per_color_floss(
            [ColorStitchCount(palette_index=0, count=100)],
            aida_count=14,
            num_strands=7,
        )
