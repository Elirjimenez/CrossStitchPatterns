from app.domain.model.pattern import Pattern, PatternGrid, Palette
from app.domain.data.dmc_colors import DmcColor
from app.application.ports.pattern_pdf_exporter import LegendEntryDTO


def make_pattern() -> Pattern:
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


def make_dmc_colors() -> list:
    return [
        DmcColor(number="321", name="Red", r=255, g=0, b=0),
        DmcColor(number="699", name="Green", r=0, g=128, b=0),
        DmcColor(number="796", name="Blue", r=0, g=0, b=255),
    ]


def make_legend_entries() -> list:
    return [
        LegendEntryDTO(
            symbol="■",
            dmc_number="321",
            dmc_name="Red",
            r=255,
            g=0,
            b=0,
            stitch_count=4,
            skeins=1,
        ),
        LegendEntryDTO(
            symbol="●",
            dmc_number="699",
            dmc_name="Green",
            r=0,
            g=128,
            b=0,
            stitch_count=4,
            skeins=1,
        ),
        LegendEntryDTO(
            symbol="▲",
            dmc_number="796",
            dmc_name="Blue",
            r=0,
            g=0,
            b=255,
            stitch_count=4,
            skeins=1,
        ),
    ]
