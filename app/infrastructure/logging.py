import structlog


def setup_logging():
    structlog.configure(
        processors=[
                structlog.processors.JSONRenderer()
        ]
    )

    logger = structlog.get_logger()
    return logger
