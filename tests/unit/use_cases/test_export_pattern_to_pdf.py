import pytest
from app.domain.model.pattern import Pattern, PatternGrid, Palette
from app.domain.data.dmc_colors import DmcColor
from app.application.use_cases.export_pattern_to_pdf import (
    ExportPdfRequest,
    ExportPdfResult,
    ExportPatternToPdf,
)


def _make_pattern() -> Pattern:
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


def _make_dmc_colors() -> list:
    return [
        DmcColor(number="321", name="Red", r=255, g=0, b=0),
        DmcColor(number="699", name="Green", r=0, g=128, b=0),
        DmcColor(number="796", name="Blue", r=0, g=0, b=255),
    ]


def test_execute_returns_pdf_bytes():
    use_case = ExportPatternToPdf()
    request = ExportPdfRequest(
        pattern=_make_pattern(),
        dmc_colors=_make_dmc_colors(),
        title="Test Pattern",
    )

    result = use_case.execute(request)

    assert isinstance(result, ExportPdfResult)
    assert isinstance(result.pdf_bytes, bytes)
    assert len(result.pdf_bytes) > 0
    assert result.pdf_bytes[:5] == b"%PDF-"


def test_result_variant_matches_request():
    use_case = ExportPatternToPdf()
    request = ExportPdfRequest(
        pattern=_make_pattern(),
        dmc_colors=_make_dmc_colors(),
        title="Test",
        variant="bw",
    )

    result = use_case.execute(request)

    assert result.variant == "bw"


def test_result_has_one_page():
    use_case = ExportPatternToPdf()
    request = ExportPdfRequest(
        pattern=_make_pattern(),
        dmc_colors=_make_dmc_colors(),
        title="Test",
    )

    result = use_case.execute(request)

    assert result.num_pages == 1


def test_rejects_empty_title():
    use_case = ExportPatternToPdf()
    request = ExportPdfRequest(
        pattern=_make_pattern(),
        dmc_colors=_make_dmc_colors(),
        title="",
    )

    with pytest.raises(ValueError):
        use_case.execute(request)


def test_rejects_invalid_variant():
    use_case = ExportPatternToPdf()
    request = ExportPdfRequest(
        pattern=_make_pattern(),
        dmc_colors=_make_dmc_colors(),
        title="Test",
        variant="grayscale",
    )

    with pytest.raises(ValueError):
        use_case.execute(request)
