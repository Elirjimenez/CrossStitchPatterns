import pytest
from app.domain.services.symbol_map import assign_symbols, contrast_color
from app.domain.exceptions import DomainException


def test_assign_symbols_returns_correct_count():
    result = assign_symbols(5)
    assert len(result) == 5


def test_assign_symbols_returns_unique_symbols():
    result = assign_symbols(10)
    assert len(set(result)) == 10


def test_assign_symbols_single_color():
    result = assign_symbols(1)
    assert len(result) == 1
    assert isinstance(result[0], str)
    assert len(result[0]) == 1


def test_assign_symbols_max_capacity():
    from app.domain.services.symbol_map import SYMBOLS

    result = assign_symbols(len(SYMBOLS))
    assert len(result) == len(SYMBOLS)
    assert len(set(result)) == len(SYMBOLS)


def test_assign_symbols_zero_raises():
    with pytest.raises(DomainException):
        assign_symbols(0)


def test_assign_symbols_negative_raises():
    with pytest.raises(DomainException):
        assign_symbols(-1)


def test_assign_symbols_exceeds_capacity_raises():
    from app.domain.services.symbol_map import SYMBOLS

    with pytest.raises(DomainException):
        assign_symbols(len(SYMBOLS) + 1)


def test_symbols_are_not_letters():
    """Symbols should be geometric/pictographic, not A-Z letters."""
    result = assign_symbols(20)
    for symbol in result:
        assert not symbol.isalpha(), f"Symbol '{symbol}' is a letter"


def test_assign_symbols_all_single_characters():
    result = assign_symbols(20)
    for symbol in result:
        assert isinstance(symbol, str)
        assert len(symbol) == 1


def test_at_least_200_symbols_available():
    """Must support 200+ colors for complex patterns."""
    from app.domain.services.symbol_map import SYMBOLS

    assert len(SYMBOLS) >= 200


def test_all_symbols_are_unique():
    from app.domain.services.symbol_map import SYMBOLS

    assert len(SYMBOLS) == len(set(SYMBOLS))


def test_contrast_color_black_returns_white():
    assert contrast_color(0, 0, 0) == (255, 255, 255)


def test_contrast_color_white_returns_black():
    assert contrast_color(255, 255, 255) == (0, 0, 0)


def test_contrast_color_red_returns_white():
    # Red is dark (luminance ~0.30)
    assert contrast_color(255, 0, 0) == (255, 255, 255)


def test_contrast_color_yellow_returns_black():
    # Yellow is light (luminance ~0.89)
    assert contrast_color(255, 255, 0) == (0, 0, 0)


def test_contrast_color_dark_green_returns_white():
    # (0, 128, 0) luminance ~0.29
    assert contrast_color(0, 128, 0) == (255, 255, 255)


def test_contrast_color_light_gray_returns_black():
    assert contrast_color(200, 200, 200) == (0, 0, 0)
