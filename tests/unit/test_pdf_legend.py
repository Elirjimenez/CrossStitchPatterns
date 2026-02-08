from io import BytesIO

import pypdf

from app.domain.services.fabric import FabricSize
from app.infrastructure.pdf_export.pdf_generator import render_pattern_pdf
from tests.helpers.pattern_fixtures import make_pattern, make_legend_entries


def _render() -> bytes:
    return render_pattern_pdf(
        pattern=make_pattern(),
        title="Test Pattern",
        fabric_size=FabricSize(width_cm=20.0, height_cm=15.0),
        aida_count=14,
        margin_cm=5.0,
        legend_entries=make_legend_entries(),
    )


def test_render_pattern_pdf_returns_valid_pdf():
    pdf_bytes = _render()
    assert pdf_bytes[:5] == b"%PDF-"


def test_render_pattern_pdf_has_two_pages():
    pdf_bytes = _render()
    reader = pypdf.PdfReader(BytesIO(pdf_bytes))
    assert len(reader.pages) == 2


def test_legend_page_contains_legend_title():
    pdf_bytes = _render()
    reader = pypdf.PdfReader(BytesIO(pdf_bytes))
    legend_text = reader.pages[1].extract_text()
    assert "Legend" in legend_text


def test_legend_page_contains_dmc_numbers():
    pdf_bytes = _render()
    reader = pypdf.PdfReader(BytesIO(pdf_bytes))
    legend_text = reader.pages[1].extract_text()
    assert "321" in legend_text
    assert "699" in legend_text
    assert "796" in legend_text


def test_legend_page_contains_dmc_names():
    pdf_bytes = _render()
    reader = pypdf.PdfReader(BytesIO(pdf_bytes))
    legend_text = reader.pages[1].extract_text()
    assert "Red" in legend_text
    assert "Green" in legend_text
    assert "Blue" in legend_text


def test_legend_page_contains_stitch_counts():
    pdf_bytes = _render()
    reader = pypdf.PdfReader(BytesIO(pdf_bytes))
    legend_text = reader.pages[1].extract_text()
    assert "4" in legend_text


def test_legend_page_contains_skeins():
    pdf_bytes = _render()
    reader = pypdf.PdfReader(BytesIO(pdf_bytes))
    legend_text = reader.pages[1].extract_text()
    assert "1" in legend_text
