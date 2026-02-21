"""Unit tests for generation safety limits (validate_generation_limits)."""

import pytest

from app.config import Settings
from app.domain.exceptions import DomainException
from app.web.validators import validate_generation_limits


def _settings(**overrides) -> Settings:
    """Build a Settings instance with limit defaults, overridable per-test."""
    base = {
        "database_url": "postgresql://user:pass@localhost/test",
        "max_colors": 20,
        "max_target_width": 300,
        "max_target_height": 300,
        "max_target_pixels": 90_000,
        "max_input_pixels": 2_000_000,
    }
    base.update(overrides)
    return Settings(**base)


class TestValidateGenerationLimitsAccepts:
    def test_accepts_values_exactly_at_limits(self):
        """Edge case: all values at their maximums must succeed."""
        validate_generation_limits(
            num_colors=20, target_w=300, target_h=300, settings=_settings()
        )

    def test_accepts_typical_small_request(self):
        validate_generation_limits(
            num_colors=10, target_w=150, target_h=100, settings=_settings()
        )

    def test_accepts_without_input_dimensions(self):
        """input_w / input_h are optional; omitting them skips that check."""
        validate_generation_limits(
            num_colors=5, target_w=100, target_h=100, settings=_settings()
        )

    def test_accepts_input_pixels_exactly_at_limit(self):
        s = _settings(max_input_pixels=1_000_000)
        # 1000 * 1000 = 1_000_000 exactly → allowed
        validate_generation_limits(
            num_colors=5, target_w=100, target_h=100, settings=s,
            input_w=1000, input_h=1000,
        )


class TestValidateGenerationLimitsRejectsColors:
    def test_rejects_num_colors_one_over_max(self):
        with pytest.raises(DomainException, match="21"):
            validate_generation_limits(
                num_colors=21, target_w=100, target_h=100, settings=_settings()
            )

    def test_rejects_num_colors_far_over_max(self):
        with pytest.raises(DomainException):
            validate_generation_limits(
                num_colors=500, target_w=50, target_h=50, settings=_settings()
            )

    def test_error_message_includes_max_colors(self):
        with pytest.raises(DomainException, match="20"):
            validate_generation_limits(
                num_colors=21, target_w=100, target_h=100, settings=_settings()
            )


class TestValidateGenerationLimitsRejectsDimensions:
    def test_rejects_target_width_one_over_max(self):
        with pytest.raises(DomainException, match="301"):
            validate_generation_limits(
                num_colors=10, target_w=301, target_h=100, settings=_settings()
            )

    def test_rejects_target_height_one_over_max(self):
        with pytest.raises(DomainException, match="301"):
            validate_generation_limits(
                num_colors=10, target_w=100, target_h=301, settings=_settings()
            )

    def test_rejects_target_pixels_over_limit(self):
        # Use max_target_pixels=50_000 so both dims can be valid individually
        # but their product exceeds the pixel limit: 250*201 = 50_250 > 50_000
        s = _settings(max_target_pixels=50_000)
        with pytest.raises(DomainException, match="pixels"):
            validate_generation_limits(
                num_colors=10, target_w=250, target_h=201, settings=s
            )

    def test_pixel_check_uses_product_not_individual_dims(self):
        # Both dims within limits, product exceeds custom pixel cap
        s = _settings(max_target_pixels=10_000)
        with pytest.raises(DomainException, match="pixels"):
            validate_generation_limits(
                num_colors=10, target_w=150, target_h=68, settings=s  # 150*68 = 10_200
            )


class TestValidateGenerationLimitsRejectsInputPixels:
    def test_rejects_input_pixels_over_limit(self):
        s = _settings(max_input_pixels=1_000_000)
        with pytest.raises(DomainException, match="input"):
            validate_generation_limits(
                num_colors=5, target_w=100, target_h=100, settings=s,
                input_w=1001, input_h=1000,
            )

    def test_no_check_when_input_dims_not_provided(self):
        # Huge max_input_pixels doesn't matter when w/h are None
        s = _settings(max_input_pixels=1)
        # Should NOT raise, because input_w/input_h are not given
        validate_generation_limits(
            num_colors=5, target_w=100, target_h=100, settings=s,
        )


class TestSettingsGenerationFields:
    """Config layer: new generation-limit fields exist with correct defaults."""

    def test_default_max_colors(self):
        assert Settings().max_colors == 20

    def test_default_max_target_width(self):
        assert Settings().max_target_width == 300

    def test_default_max_target_height(self):
        assert Settings().max_target_height == 300

    def test_default_max_target_pixels(self):
        assert Settings().max_target_pixels == 90_000

    def test_default_max_input_pixels(self):
        assert Settings().max_input_pixels == 2_000_000

    def test_overridable_via_constructor(self):
        s = Settings(max_colors=10, max_target_width=150)
        assert s.max_colors == 10
        assert s.max_target_width == 150
