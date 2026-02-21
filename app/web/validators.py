"""Web-layer validation helpers for pattern generation requests."""

from __future__ import annotations

from app.config import Settings
from app.domain.exceptions import DomainException


def validate_generation_limits(
    num_colors: int,
    target_w: int | None,
    target_h: int | None,
    settings: Settings,
    input_w: int | None = None,
    input_h: int | None = None,
) -> None:
    """Check generation parameters against the configured safety limits.

    Raises:
        DomainException: with a user-friendly message for any violated limit.
    """
    if num_colors > settings.max_colors:
        raise DomainException(
            f"Number of colors {num_colors} exceeds the maximum of {settings.max_colors}."
        )

    if target_w is not None and target_w > settings.max_target_width:
        raise DomainException(
            f"Target width {target_w} exceeds the maximum of "
            f"{settings.max_target_width} stitches."
        )

    if target_h is not None and target_h > settings.max_target_height:
        raise DomainException(
            f"Target height {target_h} exceeds the maximum of "
            f"{settings.max_target_height} stitches."
        )

    if target_w is not None and target_h is not None:
        total = target_w * target_h
        if total > settings.max_target_pixels:
            raise DomainException(
                f"Pattern size {target_w}×{target_h} = {total} pixels "
                f"exceeds the maximum of {settings.max_target_pixels} pixels."
            )

    if input_w is not None and input_h is not None:
        input_pixels = input_w * input_h
        if input_pixels > settings.max_input_pixels:
            raise DomainException(
                f"Input image {input_w}×{input_h} = {input_pixels} pixels "
                f"exceeds the maximum input size of {settings.max_input_pixels} pixels."
            )
