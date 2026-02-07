from app.domain.data.dmc_colors import DMC_COLORS, DmcColor


def test_dmc_colors_has_expected_entries():
    assert len(DMC_COLORS) == 489


def test_dmc_color_is_frozen_dataclass():
    color = DMC_COLORS["310"]
    assert isinstance(color, DmcColor)
    assert color.number == "310"
    assert color.name == "Black"
    assert color.r == 0
    assert color.g == 0
    assert color.b == 0


def test_dmc_white():
    color = DMC_COLORS["B5200"]
    assert color.name == "Snow White"
    assert color.r == 255
    assert color.g == 255
    assert color.b == 255


def test_dmc_color_rgb_in_valid_range():
    for number, color in DMC_COLORS.items():
        assert 0 <= color.r <= 255, f"DMC {number} r={color.r}"
        assert 0 <= color.g <= 255, f"DMC {number} g={color.g}"
        assert 0 <= color.b <= 255, f"DMC {number} b={color.b}"


def test_dmc_color_has_name():
    for number, color in DMC_COLORS.items():
        assert color.name, f"DMC {number} has no name"
        assert color.number == number
