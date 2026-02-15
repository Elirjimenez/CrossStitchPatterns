from __future__ import annotations

from pathlib import Path
from typing import Optional, Protocol, runtime_checkable


@runtime_checkable
class FileStorage(Protocol):
    """File storage abstraction for project files (source images, PDFs).

    All paths returned by save methods are relative to storage base directory.
    """

    def save_source_image(self, project_id: str, data: bytes, extension: str) -> str:
        """Save source image and return relative path."""
        ...

    def save_pdf(self, project_id: str, data: bytes, filename: str) -> str:
        """Save PDF and return relative path."""
        ...

    def resolve_file_for_download(self, relative_path: str) -> Optional[Path]:
        """Safely resolve a relative path for download.

        Returns absolute path if file exists and is within storage directory.
        Returns None if path is invalid, attempts traversal, or file doesn't exist.

        Security: MUST prevent directory traversal attacks.
        """
        ...
