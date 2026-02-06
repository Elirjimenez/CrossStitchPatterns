from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_calculate_fabric_returns_200():
    response = client.post("/api/patterns/calculate-fabric", json={
        "pattern_width": 140,
        "pattern_height": 100,
        "aida_count": 14,
        "margin_cm": 5.0,
        "num_colors": 8,
        "num_strands": 2,
    })

    assert response.status_code == 200
    data = response.json()

    assert round(data["fabric"]["width_cm"], 1) == 35.4
    assert round(data["fabric"]["height_cm"], 1) == 28.1
    assert data["thread"]["total_stitches"] == 14000
    assert data["thread"]["num_colors"] == 8
    assert data["thread"]["skeins_per_color"] == 2
    assert data["thread"]["total_skeins"] == 16


def test_calculate_fabric_uses_defaults():
    """Omitting optional fields uses defaults (margin=5, strands=2)."""
    response = client.post("/api/patterns/calculate-fabric", json={
        "pattern_width": 140,
        "pattern_height": 100,
        "aida_count": 14,
        "num_colors": 8,
    })

    assert response.status_code == 200
    data = response.json()
    assert data["thread"]["total_skeins"] == 16


def test_calculate_fabric_validates_input():
    """Invalid input returns 422 (Pydantic validation)."""
    response = client.post("/api/patterns/calculate-fabric", json={
        "pattern_width": 0,
        "pattern_height": 100,
        "aida_count": 14,
        "num_colors": 8,
    })

    assert response.status_code == 422
