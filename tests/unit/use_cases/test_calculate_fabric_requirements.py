import pytest
from app.application.use_cases.calculate_fabric_requirements import (
    CalculateFabricRequirements,
    FabricRequirementsRequest,
)


def test_fabric_requirements_combines_fabric_and_floss():
    """Use case returns both fabric size and floss estimate."""
    use_case = CalculateFabricRequirements()
    request = FabricRequirementsRequest(
        pattern_width=140,
        pattern_height=100,
        aida_count=14,
        margin_cm=5.0,
        num_colors=8,
        num_strands=2,
    )

    result = use_case.execute(request)

    # Fabric size: same as domain service
    assert round(result.fabric_width_cm, 1) == 35.4
    assert round(result.fabric_height_cm, 1) == 28.1

    # Floss: total_stitches = 140 * 100 = 14000
    assert result.total_stitches == 14000
    assert result.num_colors == 8
    assert result.skeins_per_color == 2
    assert result.total_skeins == 16


def test_fabric_requirements_default_strands():
    """Default num_strands should be 2."""
    use_case = CalculateFabricRequirements()
    request = FabricRequirementsRequest(
        pattern_width=140,
        pattern_height=100,
        aida_count=14,
        num_colors=8,
    )

    result = use_case.execute(request)

    assert result.total_skeins == 16


def test_fabric_requirements_rejects_invalid_input():
    """Use case propagates validation errors from domain services."""
    use_case = CalculateFabricRequirements()

    with pytest.raises(ValueError):
        use_case.execute(
            FabricRequirementsRequest(
                pattern_width=0,
                pattern_height=100,
                aida_count=14,
                num_colors=8,
            )
        )

    with pytest.raises(ValueError):
        use_case.execute(
            FabricRequirementsRequest(
                pattern_width=140,
                pattern_height=100,
                aida_count=14,
                num_colors=8,
                num_strands=7,
            )
        )
