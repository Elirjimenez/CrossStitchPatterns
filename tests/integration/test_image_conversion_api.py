import io

from PIL import Image
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _make_test_image(width: int, height: int, color: tuple = (255, 0, 0)) -> bytes:
    """Create a solid-color PNG image in memory."""
    img = Image.new("RGB", (width, height), color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_convert_pattern_returns_200():
    image_bytes = _make_test_image(20, 20, color=(128, 64, 32))
    response = client.post(
        "/api/patterns/convert",
        data={"target_width": "10", "target_height": "10", "num_colors": "3"},
        files={"file": ("test.png", image_bytes, "image/png")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["grid"]["width"] == 10
    assert data["grid"]["height"] == 10
    assert len(data["palette"]) <= 3
    assert len(data["dmc_colors"]) <= 3


def test_convert_pattern_dmc_colors_have_numbers():
    image_bytes = _make_test_image(10, 10)
    response = client.post(
        "/api/patterns/convert",
        data={"target_width": "10", "target_height": "10", "num_colors": "2"},
        files={"file": ("test.png", image_bytes, "image/png")},
    )

    assert response.status_code == 200
    data = response.json()
    for dmc in data["dmc_colors"]:
        assert "number" in dmc
        assert "name" in dmc
        assert "r" in dmc
        assert "g" in dmc
        assert "b" in dmc


def test_convert_pattern_rejects_missing_file():
    response = client.post(
        "/api/patterns/convert",
        data={"target_width": "5", "target_height": "5", "num_colors": "3"},
    )
    assert response.status_code == 422
