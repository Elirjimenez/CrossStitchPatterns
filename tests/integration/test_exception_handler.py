from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from starlette.responses import JSONResponse

from app.domain.exceptions import DomainException
from app.main import domain_exception_handler


def test_domain_exception_handler_returns_400():
    """domain_exception_handler returns HTTP 400 with detail body."""
    app = FastAPI()

    app.add_exception_handler(DomainException, domain_exception_handler)

    @app.get("/fail")
    def fail():
        raise DomainException("something went wrong")

    client = TestClient(app)
    response = client.get("/fail")

    assert response.status_code == 400
    assert response.json() == {"detail": "something went wrong"}
