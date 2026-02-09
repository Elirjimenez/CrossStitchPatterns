from __future__ import annotations

import os
from pathlib import Path


class LocalFileStorage:
    def __init__(self, base_dir: str) -> None:
        self._base_dir = Path(base_dir)

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
