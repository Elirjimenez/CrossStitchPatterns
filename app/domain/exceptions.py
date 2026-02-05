class DomainException(Exception):
    """Base domain exception"""
    pass


class InvalidPatternDimensionsError(DomainException):
    pass


class PatternNotFoundError(DomainException):
    pass
