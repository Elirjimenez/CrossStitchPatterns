class DomainException(ValueError):
    """Base domain exception."""

    pass


class InvalidPatternDimensionsError(DomainException):
    """Raised when pattern dimensions are invalid."""

    pass


class InvalidFabricParametersError(DomainException):
    """Raised when fabric or floss parameters are invalid."""

    pass


class PatternNotFoundError(DomainException):
    """Raised when a pattern is not found."""

    pass


class ProjectNotFoundError(DomainException):
    """Raised when a project is not found."""

    pass
