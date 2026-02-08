import pytest
from app.domain.services.symbol_map import assign_symbols
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
