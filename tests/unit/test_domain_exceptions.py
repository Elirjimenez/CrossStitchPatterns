import pytest
from app.domain.exceptions import (
    DomainException,
    InvalidFabricParametersError,
    InvalidPatternDimensionsError,
    PatternNotFoundError,
)


def test_domain_exception_is_value_error():
    assert issubclass(DomainException, ValueError)


def test_invalid_pattern_dimensions_is_domain_exception():
    assert issubclass(InvalidPatternDimensionsError, DomainException)


def test_invalid_fabric_parameters_is_domain_exception():
    assert issubclass(InvalidFabricParametersError, DomainException)


def test_pattern_not_found_is_domain_exception():
    assert issubclass(PatternNotFoundError, DomainException)


def test_exception_preserves_message():
    exc = InvalidPatternDimensionsError("width must be > 0")
    assert str(exc) == "width must be > 0"

    exc2 = InvalidFabricParametersError("aida_count must be > 0")
    assert str(exc2) == "aida_count must be > 0"
