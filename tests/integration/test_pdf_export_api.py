from io import BytesIO

import pypdf
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _make_export_body(**overrides) -> dict:
    body = {
        "grid": {
            "width": 4,
            "height": 3,
            "cells": [
                [0, 1, 2, 0],
                [1, 2, 0, 1],
                [2, 0, 1, 2],
            ],
        },
        "palette": [[255, 0, 0], [0, 128, 0], [0, 0, 255]],
        "dmc_colors": [
            {"number": "321", "name": "Red", "r": 255, "g": 0, "b": 0},
            {"number": "699", "name": "Green", "r": 0, "g": 128, "b": 0},
            {"number": "796", "name": "Blue", "r": 0, "g": 0, "b": 255},
        ],
        "title": "Test Pattern",
        "aida_count": 14,
        "margin_cm": 5.0,
        "variant": "color",
    }
    body.update(overrides)
    return body


def test_export_pdf_returns_200_with_pdf_content():
    response = client.post(
        "/api/patterns/export-pdf",
        json=_make_export_body(),
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content[:5] == b"%PDF-"


def test_export_pdf_has_two_pages():
    response = client.post(
        "/api/patterns/export-pdf",
        json=_make_export_body(),
    )

    reader = pypdf.PdfReader(BytesIO(response.content))
    assert len(reader.pages) == 2


def test_export_pdf_invalid_input_returns_422():
    response = client.post(
        "/api/patterns/export-pdf",
        json={"title": "incomplete"},
    )

    assert response.status_code == 422
