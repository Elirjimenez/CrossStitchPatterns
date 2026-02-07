import io

import pytest
from PIL import Image

from app.application.use_cases.convert_image_to_pattern import (
    ConvertImageRequest,
    ConvertImageResult,
    ConvertImageToPattern,
)
from app.domain.data.dmc_colors import DMC_COLORS


def _make_test_image(width: int, height: int, color: tuple = (255, 0, 0)) -> bytes:
    """Create a solid-color PNG image in memory."""
    img = Image.new("RGB", (width, height), color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_convert_returns_valid_pattern():
    use_case = ConvertImageToPattern()
    request = ConvertImageRequest(
        image_data=_make_test_image(10, 10),
        target_width=4,
        target_height=4,
        num_colors=3,
    )
    result = use_case.execute(request)

    assert isinstance(result, ConvertImageResult)
    assert result.pattern.grid.width == 4
    assert result.pattern.grid.height == 4
    assert len(result.pattern.palette.colors) <= 3


def test_convert_dmc_colors_match_palette():
    use_case = ConvertImageToPattern()
    request = ConvertImageRequest(
        image_data=_make_test_image(10, 10),
        target_width=2,
        target_height=2,
        num_colors=4,
    )
    result = use_case.execute(request)

    assert len(result.dmc_colors) == len(result.pattern.palette.colors)
    for i, dmc in enumerate(result.dmc_colors):
        assert (dmc.r, dmc.g, dmc.b) == result.pattern.palette.colors[i]


def test_convert_palette_colors_are_valid_dmc():
    use_case = ConvertImageToPattern()
    request = ConvertImageRequest(
        image_data=_make_test_image(10, 10, color=(0, 128, 255)),
        target_width=3,
        target_height=3,
        num_colors=4,
    )
    result = use_case.execute(request)

    dmc_rgb_set = {(c.r, c.g, c.b) for c in DMC_COLORS.values()}
    for color in result.pattern.palette.colors:
        assert color in dmc_rgb_set


def test_convert_rejects_invalid_image():
    use_case = ConvertImageToPattern()
    request = ConvertImageRequest(
        image_data=b"not an image",
        target_width=4,
        target_height=4,
        num_colors=3,
    )
    with pytest.raises(ValueError):
        use_case.execute(request)
