from __future__ import annotations
from typing import Protocol, List, Tuple

from app.domain.model.pattern import RGB


class ImageResizer(Protocol):
    def load_and_resize(self, image_bytes: bytes, width: int, height: int) -> List[List[RGB]]: ...
    def get_image_size(self, image_bytes: bytes) -> Tuple[int, int]: ...
