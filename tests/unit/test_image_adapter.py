import io

import pytest
from PIL import Image

from app.infrastructure.image_processing.image_converter import load_and_resize


def _make_test_image(width: int, height: int, color: tuple = (255, 0, 0)) -> bytes:
    """Create a solid-color PNG image in memory."""
    img = Image.new("RGB", (width, height), color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_load_and_resize_returns_correct_dimensions():
    image_bytes = _make_test_image(100, 80)
    pixels = load_and_resize(image_bytes, width=10, height=8)
    assert len(pixels) == 8  # height
    assert len(pixels[0]) == 10  # width


def test_load_and_resize_returns_rgb_tuples():
    image_bytes = _make_test_image(10, 10, color=(128, 64, 32))
    pixels = load_and_resize(image_bytes, width=5, height=5)
    r, g, b = pixels[0][0]
    assert isinstance(r, int)
    assert isinstance(g, int)
    assert isinstance(b, int)


def test_load_and_resize_solid_color():
    image_bytes = _make_test_image(10, 10, color=(255, 0, 0))
    pixels = load_and_resize(image_bytes, width=3, height=3)
    for row in pixels:
        for pixel in row:
            assert pixel == (255, 0, 0)


def test_load_and_resize_rejects_invalid_data():
    with pytest.raises(ValueError):
        load_and_resize(b"not an image", width=10, height=10)


def test_load_and_resize_rejects_invalid_dimensions():
    image_bytes = _make_test_image(10, 10)
    with pytest.raises(ValueError):
        load_and_resize(image_bytes, width=0, height=10)
    with pytest.raises(ValueError):
        load_and_resize(image_bytes, width=10, height=0)
