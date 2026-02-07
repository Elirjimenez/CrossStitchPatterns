from app.infrastructure.logging import setup_logging


def test_setup_logging_returns_logger():
    logger = setup_logging()
    assert hasattr(logger, "info")
    assert hasattr(logger, "error")
    assert hasattr(logger, "warning")
