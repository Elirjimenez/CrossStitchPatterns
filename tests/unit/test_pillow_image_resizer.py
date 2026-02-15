"""Tests for PillowImageResizer - PIL/Pillow adapter for image processing."""

import io

import pytest
from PIL import Image

from app.infrastructure.image_processing.pillow_image_resizer import (
    PillowImageResizer,
)


def _make_test_image(width: int, height: int, color: tuple = (255, 0, 0)) -> bytes:
    """Create a solid-color PNG image in memory."""
    img = Image.new("RGB", (width, height), color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class TestGetImageSize:
    """Tests for get_image_size method."""

    def test_returns_correct_size_for_valid_image(self):
        """Should return (width, height) for valid image."""
        resizer = PillowImageResizer()
        image_bytes = _make_test_image(100, 80)

        size = resizer.get_image_size(image_bytes)

        assert size == (100, 80)

    def test_raises_value_error_for_invalid_data(self):
        """Should raise ValueError for invalid image data."""
        resizer = PillowImageResizer()

        with pytest.raises(ValueError) as exc_info:
            resizer.get_image_size(b"not an image")

        assert "Invalid image data" in str(exc_info.value)

    def test_raises_value_error_for_empty_bytes(self):
        """Should raise ValueError for empty byte string."""
        resizer = PillowImageResizer()

        with pytest.raises(ValueError) as exc_info:
            resizer.get_image_size(b"")

        assert "Invalid image data" in str(exc_info.value)

    def test_raises_value_error_for_corrupted_image(self):
        """Should raise ValueError for corrupted image data."""
        resizer = PillowImageResizer()
        # Create corrupted PNG (starts with PNG header but is invalid)
        corrupted = b"\x89PNG\r\n\x1a\n" + b"corrupted data"

        with pytest.raises(ValueError) as exc_info:
            resizer.get_image_size(corrupted)

        assert "Invalid image data" in str(exc_info.value)


class TestLoadAndResize:
    """Tests for load_and_resize method."""

    def test_returns_correct_dimensions(self):
        """Should return pixels with requested dimensions."""
        resizer = PillowImageResizer()
        image_bytes = _make_test_image(100, 80)

        pixels = resizer.load_and_resize(image_bytes, width=10, height=8)

        assert len(pixels) == 8  # height
        assert len(pixels[0]) == 10  # width

    def test_returns_rgb_tuples(self):
        """Should return RGB tuples for each pixel."""
        resizer = PillowImageResizer()
        image_bytes = _make_test_image(10, 10, color=(128, 64, 32))

        pixels = resizer.load_and_resize(image_bytes, width=5, height=5)

        r, g, b = pixels[0][0]
        assert isinstance(r, int)
        assert isinstance(g, int)
        assert isinstance(b, int)
        assert 0 <= r <= 255
        assert 0 <= g <= 255
        assert 0 <= b <= 255

    def test_solid_color_image(self):
        """Should preserve solid colors correctly."""
        resizer = PillowImageResizer()
        image_bytes = _make_test_image(10, 10, color=(255, 0, 0))

        pixels = resizer.load_and_resize(image_bytes, width=3, height=3)

        for row in pixels:
            for pixel in row:
                assert pixel == (255, 0, 0)

    def test_raises_value_error_for_zero_width(self):
        """Should raise ValueError when width is zero."""
        resizer = PillowImageResizer()
        image_bytes = _make_test_image(10, 10)

        with pytest.raises(ValueError) as exc_info:
            resizer.load_and_resize(image_bytes, width=0, height=10)

        assert "width and height must be > 0" in str(exc_info.value)

    def test_raises_value_error_for_zero_height(self):
        """Should raise ValueError when height is zero."""
        resizer = PillowImageResizer()
        image_bytes = _make_test_image(10, 10)

        with pytest.raises(ValueError) as exc_info:
            resizer.load_and_resize(image_bytes, width=10, height=0)

        assert "width and height must be > 0" in str(exc_info.value)

    def test_raises_value_error_for_negative_width(self):
        """Should raise ValueError when width is negative."""
        resizer = PillowImageResizer()
        image_bytes = _make_test_image(10, 10)

        with pytest.raises(ValueError) as exc_info:
            resizer.load_and_resize(image_bytes, width=-5, height=10)

        assert "width and height must be > 0" in str(exc_info.value)

    def test_raises_value_error_for_negative_height(self):
        """Should raise ValueError when height is negative."""
        resizer = PillowImageResizer()
        image_bytes = _make_test_image(10, 10)

        with pytest.raises(ValueError) as exc_info:
            resizer.load_and_resize(image_bytes, width=10, height=-5)

        assert "width and height must be > 0" in str(exc_info.value)

    def test_raises_value_error_for_invalid_image_data(self):
        """Should raise ValueError for invalid image data."""
        resizer = PillowImageResizer()

        with pytest.raises(ValueError) as exc_info:
            resizer.load_and_resize(b"not an image", width=10, height=10)

        assert "Invalid image data" in str(exc_info.value)

    def test_raises_value_error_for_empty_bytes(self):
        """Should raise ValueError for empty byte string."""
        resizer = PillowImageResizer()

        with pytest.raises(ValueError) as exc_info:
            resizer.load_and_resize(b"", width=10, height=10)

        assert "Invalid image data" in str(exc_info.value)

    def test_raises_value_error_for_corrupted_image(self):
        """Should raise ValueError for corrupted image data."""
        resizer = PillowImageResizer()
        # Create corrupted PNG
        corrupted = b"\x89PNG\r\n\x1a\n" + b"corrupted data"

        with pytest.raises(ValueError) as exc_info:
            resizer.load_and_resize(corrupted, width=10, height=10)

        assert "Invalid image data" in str(exc_info.value)

    def test_resizes_large_image_down(self):
        """Should correctly downsize a large image."""
        resizer = PillowImageResizer()
        image_bytes = _make_test_image(1000, 800)

        pixels = resizer.load_and_resize(image_bytes, width=10, height=8)

        assert len(pixels) == 8
        assert len(pixels[0]) == 10

    def test_resizes_small_image_up(self):
        """Should correctly upscale a small image."""
        resizer = PillowImageResizer()
        image_bytes = _make_test_image(5, 5)

        pixels = resizer.load_and_resize(image_bytes, width=20, height=20)

        assert len(pixels) == 20
        assert len(pixels[0]) == 20
