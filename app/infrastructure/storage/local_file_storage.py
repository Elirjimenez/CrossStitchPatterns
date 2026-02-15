from __future__ import annotations

import os
from pathlib import Path


class LocalFileStorage:
    def __init__(self, base_dir: str) -> None:
        self._base_dir = Path(base_dir)

    def get_file_path(self, relative_path: str) -> Path:
        """Get the absolute path for a file given its relative storage path."""
        return self._base_dir / relative_path

    def file_exists(self, relative_path: str) -> bool:
        """Check if a file exists in storage."""
        file_path = self.get_file_path(relative_path)
        return file_path.exists() and file_path.is_file()

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

    def _ensure_project_dir(self, project_id: str) -> Path:
        project_dir = self._base_dir / "projects" / project_id
        project_dir.mkdir(parents=True, exist_ok=True)
        return project_dir
