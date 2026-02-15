from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


class LocalFileStorage:
    """Local filesystem storage with path traversal protection."""

    ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".pdf"}

    def __init__(self, base_dir: str) -> None:
        self._base_dir = Path(base_dir).resolve()
        # Ensure base directory exists
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def save_source_image(self, project_id: str, data: bytes, extension: str) -> str:
        if not extension.startswith("."):
            extension = f".{extension}"
        project_dir = self._ensure_project_dir(project_id)
        filename = f"source{extension}"
        file_path = project_dir / filename
        file_path.write_bytes(data)
        return str(file_path.relative_to(self._base_dir))

    def save_pdf(self, project_id: str, data: bytes, filename: str) -> str:
        project_dir = self._ensure_project_dir(project_id)
        file_path = project_dir / filename
        file_path.write_bytes(data)
        return str(file_path.relative_to(self._base_dir))

    def resolve_file_for_download(self, relative_path: str) -> Optional[Path]:
        """Safely resolve a relative path for download with traversal protection.

        Returns:
            Absolute Path if file exists and is within storage base directory.
            None if path is invalid, outside base dir, or file doesn't exist.
        """
        try:
            # Normalize the relative path (remove .., etc.)
            requested_path = Path(relative_path)

            # Join with base directory and resolve to absolute path
            absolute_path = (self._base_dir / requested_path).resolve()

            # SECURITY: Verify resolved path is within base directory
            # Using try/except for Python < 3.9 compatibility
            try:
                # Python >= 3.9
                if not absolute_path.is_relative_to(self._base_dir):
                    return None
            except AttributeError:
                # Python < 3.9 fallback
                try:
                    absolute_path.relative_to(self._base_dir)
                except ValueError:
                    return None

            # Check file exists and is a regular file (not directory)
            if not absolute_path.exists() or not absolute_path.is_file():
                return None

            # Optional: Validate file extension
            if absolute_path.suffix.lower() not in self.ALLOWED_EXTENSIONS:
                return None

            return absolute_path

        except (ValueError, OSError):
            # Invalid path, permission errors, etc.
            return None

    def _ensure_project_dir(self, project_id: str) -> Path:
        project_dir = self._base_dir / "projects" / project_id
        project_dir.mkdir(parents=True, exist_ok=True)
        return project_dir
