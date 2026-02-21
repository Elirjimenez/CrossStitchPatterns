from __future__ import annotations

import os
import re
import shutil
from pathlib import Path
from typing import Optional


class LocalFileStorage:
    """Local filesystem storage with path traversal protection."""

    # Default constants (can be overridden via constructor)
    DEFAULT_MAX_FILENAME_LENGTH = 255
    DEFAULT_ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".pdf"}

    def __init__(
        self,
        base_dir: str,
        max_filename_length: int = DEFAULT_MAX_FILENAME_LENGTH,
        allowed_extensions: Optional[set[str]] = None,
    ) -> None:
        self._base_dir = Path(base_dir).resolve()
        self._max_filename_length = max_filename_length
        self._allowed_extensions = (
            allowed_extensions
            if allowed_extensions is not None
            else self.DEFAULT_ALLOWED_EXTENSIONS
        )
        # Ensure base directory exists
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent security issues and filesystem errors.

        - Removes path separators (/, \\)
        - Removes null bytes
        - Replaces dangerous characters with underscores
        - Limits length to prevent filesystem issues
        - Preserves file extension

        Args:
            filename: Original filename

        Returns:
            Sanitized filename safe for filesystem use
        """
        max_length = self._max_filename_length
        # Remove path separators and null bytes
        filename = filename.replace("/", "_").replace("\\", "_").replace("\0", "")

        # Split into name and extension
        name_parts = filename.rsplit(".", 1)
        if len(name_parts) == 2:
            name, ext = name_parts
            ext = f".{ext}"
        else:
            name = filename
            ext = ""

        # Replace dangerous characters with underscores
        # Keep only: alphanumeric, dash, underscore, dot
        name = re.sub(r"[^\w\-.]", "_", name)

        # Remove leading/trailing dots and spaces
        name = name.strip(". ")

        # Prevent empty names
        if not name:
            name = "file"

        # Limit length (reserve space for extension)
        max_name_length = max_length - len(ext)
        if len(name) > max_name_length:
            name = name[:max_name_length]

        return f"{name}{ext}"

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
        safe_filename = self._sanitize_filename(filename)
        file_path = project_dir / safe_filename
        file_path.write_bytes(data)
        return str(file_path.relative_to(self._base_dir))

    def read_source_image(self, project_id: str, ref: str) -> bytes:
        """Read and return source image bytes for the given ref.

        Args:
            project_id: The project identifier (unused in path resolution, kept for API symmetry).
            ref: Relative storage path as returned by save_source_image.

        Raises:
            ValueError: If ref attempts directory traversal outside base directory.
            FileNotFoundError: If the file does not exist.
        """
        absolute_path = (self._base_dir / ref).resolve()

        # Security: verify resolved path is within base directory
        try:
            if not absolute_path.is_relative_to(self._base_dir):
                raise ValueError(f"Invalid ref — path traversal detected: {ref!r}")
        except AttributeError:
            # Python < 3.9 fallback
            try:
                absolute_path.relative_to(self._base_dir)
            except ValueError:
                raise ValueError(f"Invalid ref — path traversal detected: {ref!r}")

        if not absolute_path.exists() or not absolute_path.is_file():
            raise FileNotFoundError(f"Source image not found: {ref!r}")

        return absolute_path.read_bytes()

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

            # Validate file extension
            if absolute_path.suffix.lower() not in self._allowed_extensions:
                return None

            return absolute_path

        except (ValueError, OSError):
            # Invalid path, permission errors, etc.
            return None

    @staticmethod
    def _sanitize_project_id(project_id: str) -> str:
        """Sanitize project ID for use as directory name.

        Project IDs are typically UUIDs or alphanumeric strings.
        This ensures they're safe for filesystem use.
        """
        # Keep only alphanumeric, dash, underscore
        sanitized = re.sub(r"[^\w\-]", "_", project_id)
        # Prevent empty IDs
        if not sanitized:
            raise ValueError("Invalid project_id: cannot be empty after sanitization")
        return sanitized

    def delete_project_folder(self, project_id: str) -> None:
        """Delete the project's storage directory (no-op if it doesn't exist)."""
        safe_project_id = self._sanitize_project_id(project_id)
        project_dir = self._base_dir / "projects" / safe_project_id
        shutil.rmtree(project_dir, ignore_errors=True)

    def _ensure_project_dir(self, project_id: str) -> Path:
        safe_project_id = self._sanitize_project_id(project_id)
        project_dir = self._base_dir / "projects" / safe_project_id
        project_dir.mkdir(parents=True, exist_ok=True)
        return project_dir
