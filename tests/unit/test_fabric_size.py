import pytest
from app.domain.services.fabric import compute_fabric_size_cm

def test_fabric_size_14ct_with_margin():
    # 140 stitches at 14ct = 10 inches => 25.4 cm
    # with 5cm margin each side => +10cm
    size = compute_fabric_size_cm(stitches_w=140, stitches_h=70, aida_count=14, margin_cm=5)

    assert round(size.width_cm, 1) == 35.4  # 25.4 + 10
    assert round(size.height_cm, 1) == 22.7  # (70/14=5in=12.7cm)+10 => 22.7

def test_fabric_size_rejects_invalid_inputs():
    with pytest.raises(ValueError):
        compute_fabric_size_cm(0, 10, 14)
    with pytest.raises(ValueError):
        compute_fabric_size_cm(10, 10, 0)
    with pytest.raises(ValueError):
        compute_fabric_size_cm(10, 10, 14, margin_cm=-1)
