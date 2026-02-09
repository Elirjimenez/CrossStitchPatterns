from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class FileStorage(Protocol):
    def save_source_image(self, project_id: str, data: bytes, extension: str) -> str: ...

    def save_pdf(self, project_id: str, data: bytes, filename: str) -> str: ...
