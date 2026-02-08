from io import BytesIO

from pypdf import PdfReader

from app.domain.model.pattern import Pattern, PatternGrid, Palette
from app.domain.services.fabric import FabricSize
from app.infrastructure.pdf_export.pdf_generator import render_overview_page


def _make_pattern() -> Pattern:
    """Small 4x3 pattern with 3 colors for testing."""
    grid = PatternGrid(
        width=4,
        height=3,
        cells=[
            [0, 1, 2, 0],
            [1, 2, 0, 1],
            [2, 0, 1, 2],
        ],
    )
    palette = Palette(colors=[(255, 0, 0), (0, 128, 0), (0, 0, 255)])
    return Pattern(grid=grid, palette=palette)


def _extract_text(pdf_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(pdf_bytes))
    return "".join(page.extract_text() or "" for page in reader.pages)


def test_render_overview_produces_pdf_bytes():
    pattern = _make_pattern()
    fabric_size = FabricSize(width_cm=17.3, height_cm=15.4)

    result = render_overview_page(
        pattern=pattern,
        title="Test Pattern",
        fabric_size=fabric_size,
        aida_count=14,
        margin_cm=5.0,
    )

    assert isinstance(result, bytes)
    assert result[:5] == b"%PDF-"


def test_render_overview_contains_title():
    pattern = _make_pattern()
    fabric_size = FabricSize(width_cm=17.3, height_cm=15.4)

    result = render_overview_page(
        pattern=pattern,
        title="My Cross Stitch",
        fabric_size=fabric_size,
        aida_count=14,
        margin_cm=5.0,
    )

    text = _extract_text(result)
    assert "My Cross Stitch" in text


def test_render_overview_contains_stitch_dimensions():
    pattern = _make_pattern()
    fabric_size = FabricSize(width_cm=17.3, height_cm=15.4)

    result = render_overview_page(
        pattern=pattern,
        title="Test",
        fabric_size=fabric_size,
        aida_count=14,
        margin_cm=5.0,
    )

    text = _extract_text(result)
    assert "4 x 3 stitches" in text


def test_render_overview_contains_fabric_info():
    pattern = _make_pattern()
    fabric_size = FabricSize(width_cm=17.3, height_cm=15.4)

    result = render_overview_page(
        pattern=pattern,
        title="Test",
        fabric_size=fabric_size,
        aida_count=14,
        margin_cm=5.0,
    )

    text = _extract_text(result)
    assert "17.3 x 15.4 cm" in text
    assert "14ct" in text


def test_render_overview_is_single_page():
    pattern = _make_pattern()
    fabric_size = FabricSize(width_cm=17.3, height_cm=15.4)

    result = render_overview_page(
        pattern=pattern,
        title="Test",
        fabric_size=fabric_size,
        aida_count=14,
        margin_cm=5.0,
    )

    reader = PdfReader(BytesIO(result))
    assert len(reader.pages) == 1
