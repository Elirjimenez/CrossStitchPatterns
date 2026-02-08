from io import BytesIO

import pypdf

from app.application.use_cases.export_pattern_to_pdf import ExportPatternToPdf, ExportPdfRequest
from app.infrastructure.pdf_export.pattern_pdf_exporter import ReportLabPatternPdfExporter
from tests.helpers.pattern_fixtures import make_pattern, make_dmc_colors


def test_pdf_contains_legend_page():
    use_case = ExportPatternToPdf(exporter=ReportLabPatternPdfExporter())
    request = ExportPdfRequest(
        pattern=make_pattern(),
        dmc_colors=make_dmc_colors(),
        title="Test",
    )

    result = use_case.execute(request)

    reader = pypdf.PdfReader(BytesIO(result.pdf_bytes))
    assert len(reader.pages) >= 2
