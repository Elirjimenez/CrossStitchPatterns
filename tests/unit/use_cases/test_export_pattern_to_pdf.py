import pytest

from app.application.use_cases.export_pattern_to_pdf import (
    ExportPdfRequest,
    ExportPdfResult,
    ExportPatternToPdf,
)
from app.application.ports.pattern_pdf_exporter import PatternPdfExporter
from tests.helpers.pattern_fixtures import make_pattern, make_dmc_colors


class FakePatternPdfExporter(PatternPdfExporter):
    def render(
        self,
        pattern,
        title,
        fabric_size,
        aida_count,
        margin_cm,
        legend_entries,
        variant="color",
        symbols=None,
        tiles=None,
    ) -> bytes:
        return b"%PDF-FAKE"


def test_execute_returns_pdf_bytes():
    use_case = ExportPatternToPdf(exporter=FakePatternPdfExporter())
    request = ExportPdfRequest(
        pattern=make_pattern(),
        dmc_colors=make_dmc_colors(),
        title="Test Pattern",
    )

    result = use_case.execute(request)

    assert isinstance(result, ExportPdfResult)
    assert isinstance(result.pdf_bytes, bytes)
    assert len(result.pdf_bytes) > 0
    assert result.pdf_bytes[:5] == b"%PDF-"


def test_result_variant_matches_request():
    use_case = ExportPatternToPdf(exporter=FakePatternPdfExporter())
    request = ExportPdfRequest(
        pattern=make_pattern(),
        dmc_colors=make_dmc_colors(),
        title="Test",
        variant="bw",
    )

    result = use_case.execute(request)

    assert result.variant == "bw"


def test_result_has_three_pages_for_small_pattern():
    """4×3 pattern → 1 grid tile → 2 (overview+legend) + 1 = 3 pages."""
    use_case = ExportPatternToPdf(exporter=FakePatternPdfExporter())
    request = ExportPdfRequest(
        pattern=make_pattern(),
        dmc_colors=make_dmc_colors(),
        title="Test",
    )

    result = use_case.execute(request)

    assert result.num_pages == 3


def test_rejects_empty_title():
    use_case = ExportPatternToPdf(exporter=FakePatternPdfExporter())
    request = ExportPdfRequest(
        pattern=make_pattern(),
        dmc_colors=make_dmc_colors(),
        title="",
    )

    with pytest.raises(ValueError):
        use_case.execute(request)


def test_rejects_invalid_variant():
    use_case = ExportPatternToPdf(exporter=FakePatternPdfExporter())
    request = ExportPdfRequest(
        pattern=make_pattern(),
        dmc_colors=make_dmc_colors(),
        title="Test",
        variant="grayscale",
    )

    with pytest.raises(ValueError):
        use_case.execute(request)
