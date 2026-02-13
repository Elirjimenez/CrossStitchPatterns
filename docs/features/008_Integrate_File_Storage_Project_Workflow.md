# Plan: Integrate File Storage into Project Workflow

## Context

The `feature/persistence-layer` branch has `LocalFileStorage` + `FileStorage` protocol implemented and tested, but they're not wired into the actual workflow. Projects accept `source_image_ref` and `pdf_ref` as strings, but no endpoint actually saves files to storage and persists the references. This plan closes that gap.

**New branch**: `feature/file-storage-integration` (from `feature/persistence-layer`)

## Current State (on `feature/persistence-layer`)

- `FileStorage` protocol: `app/application/ports/file_storage.py` — `save_source_image()`, `save_pdf()`
- `LocalFileStorage`: `app/infrastructure/storage/local_file_storage.py` — saves to `storage/projects/{id}/`
- `ProjectRepository`: `add`, `get`, `list_all`, `update_status` — **no method to update source_image_ref**
- `PatternResultRepository`: `add`, `list_by_project`, `get_latest_by_project`
- `SavePatternResult` use case already accepts `pdf_ref: Optional[str]`
- `CreateProject` use case already accepts `source_image_ref: Optional[str]`
- DI: only `get_db_session()` in `dependencies.py` — no FileStorage wiring
- Config: no `storage_dir` setting

## Changes

### 1. Add `storage_dir` to Settings
**File**: `app/config.py`

Add `storage_dir: str = "storage"` to the `Settings` class.

### 2. Add `get_file_storage()` dependency
**File**: `app/web/api/dependencies.py`

New function that returns `LocalFileStorage(get_settings().storage_dir)`. Follows the same pattern as `get_db_session()`.

### 3. Add `update_source_image_ref()` to ProjectRepository
**Files**:
- `app/domain/repositories/project_repository.py` — add abstract method
- `app/infrastructure/persistence/sqlalchemy_project_repository.py` — implement
- `tests/helpers/in_memory_repositories.py` — implement for tests

```python
@abstractmethod
def update_source_image_ref(self, project_id: str, ref: str) -> None:
    pass
```

### 4. New endpoint: Upload source image
**File**: `app/web/api/routes/projects.py`

```
POST /api/projects/{project_id}/source-image
Content-Type: multipart/form-data
Body: file (UploadFile)
Response: 200 ProjectResponse (with updated source_image_ref)
```

Logic:
1. Validate project exists (via repo)
2. Read file bytes, extract extension from filename
3. Call `file_storage.save_source_image(project_id, data, extension)` → ref
4. Call `project_repo.update_source_image_ref(project_id, ref)`
5. Return updated project

### 5. New endpoint: Create pattern result with PDF upload
**File**: `app/web/api/routes/projects.py`

```
POST /api/projects/{project_id}/patterns/with-pdf
Content-Type: multipart/form-data
Body: file (UploadFile), palette (JSON string), grid_width (int), grid_height (int), stitch_count (int)
Response: 201 PatternResultResponse (with pdf_ref)
```

Logic:
1. Read PDF file bytes
2. Call `file_storage.save_pdf(project_id, data, "pattern.pdf")` → ref
3. Delegate to `SavePatternResult` use case with `pdf_ref=ref`

The existing JSON endpoint `POST /api/projects/{id}/patterns` stays unchanged for backward compatibility.

### 6. Unit tests (TDD)
**File**: `tests/unit/test_upload_image.py` (~5 tests)
- Upload saves file and updates project's source_image_ref
- Upload with project not found returns error
- Upload extracts correct extension

**File**: `tests/unit/test_create_pattern_with_pdf.py` (~4 tests)
- Upload saves PDF and creates pattern result with pdf_ref
- Pattern result fields match input
- Project not found returns error

### 7. Integration tests
**File**: `tests/integration/test_projects_api.py` (add to existing)
- `TestUploadSourceImage` — 3 tests via TestClient (success, not found, no file)
- `TestCreatePatternWithPdf` — 2 tests via TestClient (success, project not found)

Override `get_file_storage` in the test fixture with a `LocalFileStorage` pointed at a temp directory.

## Files Modified

| File | Action |
|------|--------|
| `app/config.py` | Add `storage_dir` setting |
| `app/web/api/dependencies.py` | Add `get_file_storage()` |
| `app/domain/repositories/project_repository.py` | Add `update_source_image_ref()` |
| `app/infrastructure/persistence/sqlalchemy_project_repository.py` | Implement `update_source_image_ref()` |
| `tests/helpers/in_memory_repositories.py` | Implement `update_source_image_ref()` |
| `app/web/api/routes/projects.py` | Add 2 new endpoints |
| `tests/unit/test_upload_image.py` | **New** — unit tests |
| `tests/unit/test_create_pattern_with_pdf.py` | **New** — unit tests |
| `tests/integration/test_projects_api.py` | Add integration tests + fixture override |

## Verification

```bash
# Switch to new branch
git checkout -b feature/file-storage-integration feature/persistence-layer

# Run all tests
pytest -v --tb=short

# Run just the new tests
pytest tests/unit/test_upload_image.py tests/unit/test_create_pattern_with_pdf.py tests/integration/test_projects_api.py -v

# Check formatting
black app/ tests/
```
