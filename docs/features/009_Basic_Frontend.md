# Feature 009 — Basic Frontend (FastAPI + Jinja2 + HTMX + Tailwind)

## Overview

This document describes the plan and implementation of the server-rendered frontend for the Cross-Stitch Pattern Generator.

The frontend is built progressively across five tasks, each independently branched, tested, and merged. All tasks follow the project's **Clean Architecture** and **TDD** rules: web routes call application use cases directly (no internal HTTP calls to `/api`), and tests are written before the implementation.

---

## Technology Stack

| Concern | Choice | Rationale |
|---|---|---|
| Routing & templates | FastAPI + Jinja2 | Native FastAPI integration, no extra framework |
| Interactivity | HTMX (CDN) | Dynamic UX without a JS framework |
| Styling | Tailwind CSS (CDN) | No build step required for the TFM scope |
| Testing | FastAPI `TestClient` + SQLite in-memory | Mirrors existing integration test pattern |

**Constraints:**
- No React/Vue — HTML is rendered server-side.
- Tailwind and HTMX via CDN only — no npm, no build pipeline.
- Web routes call application use cases directly; no HTTP self-calls to `/api`.
- TDD cycle: failing tests → implementation → full suite green.

---

## File Structure

```
app/web/
├── routes.py                          # All HTML + HTMX web routes
├── static/                            # Static assets (CSS, images)
└── templates/
    ├── base.html                      # Shared layout (Tailwind + HTMX CDN, navbar, footer)
    ├── home.html                      # Landing page
    ├── projects.html                  # Projects list + create form
    ├── project_detail.html            # Project detail page
    ├── project_not_found.html         # 404 / 500 error page
    └── partials/
        ├── projects_list.html         # HTMX partial: project rows / empty / error state
        ├── flash.html                 # HTMX partial: success / error alert message
        └── source_image_card.html     # HTMX partial: source image upload card

tests/integration/
└── test_web_routes.py                 # Integration tests for all web routes
```

---

## Task 1 — Frontend Skeleton & Base Layout

**Branch:** `feature/frontend-task1-skeleton-base-layout`

### Goal

Bootstrap the Jinja2 + HTMX + Tailwind stack and confirm a styled HTML page renders correctly.

### Deliverables

**`app/main.py`** — wire frontend into app startup:
- Mount `StaticFiles` at `/static`.
- Include the web `APIRouter` (separate from the existing `/api` router).

**`app/web/routes.py`** — HTML routes:
- `GET /` → `home.html`
- `GET /projects` → `projects.html` (placeholder)

**`base.html`** — shared layout:
- Tailwind CSS CDN
- HTMX CDN
- Navbar with links: Home, Projects
- `{% block content %}` for page-specific HTML

**`home.html`** — landing page:
- Title: "Cross-Stitch Pattern Generator"
- Short subtitle
- CTA buttons: "View Projects", "API Docs"

**`projects.html`** — placeholder for Task 2.

**`requirements.txt`** — add `jinja2==3.1.4`.

### Quality Checks

- App starts without errors.
- `GET /` → 200, renders home page with correct title.
- `GET /projects` → 200, renders placeholder.
- Existing `/api` routes are unaffected.

---

## Task 2 — Projects List Page (HTMX)

**Branch:** `feature/frontend-task2-projects-list`

### Goal

Replace the placeholder projects page with a real, dynamically loaded list using HTMX.

### Design Decisions

- The HTMX endpoint `GET /hx/projects` calls the `ListProjects` use case directly — no internal HTTP call to `/api/projects`. This avoids round-trip overhead and the need for `httpx`.
- The `#projects-list` container loads its content on page load via `hx-trigger="load"`.

### Deliverables

**`partials/projects_list.html`** — three states:

| State | Trigger | Content |
|---|---|---|
| Populated | Projects exist | Table: name, status badge, created date, "View →" link |
| Empty | No projects | Friendly message + "Go to Home" button |
| Error | Repository raises | Red alert + "Retry" button (re-fires `hx-get`) |

**`GET /hx/projects`** in `routes.py`:
- Calls `ListProjects(project_repo=repo)`.
- Returns `partials/projects_list.html`.
- On exception: logs with structlog, returns error state (HTTP 200 so HTMX renders it).

**`projects.html`** — updated:
```html
<div id="projects-list"
     hx-get="/hx/projects"
     hx-trigger="load"
     hx-target="#projects-list"
     hx-swap="innerHTML"
     hx-indicator="#projects-loading">
</div>
```

### Quality Checks

- `GET /projects` → 200, contains HTMX attributes.
- `GET /hx/projects` (empty DB) → 200, shows empty state.
- `GET /hx/projects` (with projects) → 200, shows project rows with correct badges.
- `GET /hx/projects` (broken repo) → 200, shows error state with Retry button.

---

## Task 3 — Create Project (HTMX)

**Branch:** `feature/frontend-task3-create-project`

### Goal

Add a "New Project" form to the projects page. Submit via HTMX and refresh the list on success — no page reload.

### Design Decisions

- Success response sets `HX-Trigger: {"projectsChanged": true}` header.
- The `#projects-list` container listens with `hx-trigger="load, projectsChanged from:body"` so it reloads automatically.
- Validation happens in two layers: web layer (blank name check) and domain layer (`Project.__post_init__` raises `DomainException`).

### Deliverables

**`partials/flash.html`** — reusable alert partial:

| Variable | Effect |
|---|---|
| `success=True` | Green alert with message |
| `success=False` | Red alert with message |

**`projects.html`** — updated with:
- Create Project card containing a `name` input and submit button.
- `hx-post="/hx/projects/create"`, `hx-target="#project-form-feedback"`, `hx-swap="innerHTML"`.
- `<div id="project-form-feedback">` to receive the flash partial.
- Updated `hx-trigger` on `#projects-list` to include `projectsChanged from:body`.

**`POST /hx/projects/create`** in `routes.py`:

| Condition | Response |
|---|---|
| Blank name | `flash.html` (error), HTTP 400 |
| `DomainException` | `flash.html` (error), HTTP 400 |
| Success | `flash.html` (success) + `HX-Trigger: projectsChanged`, HTTP 200 |
| Unexpected error | `flash.html` (error) + structlog, HTTP 500 |

### Quality Checks

- Valid name → success flash + list refreshes with new project.
- Blank name → error flash, no project created.
- Whitespace-only name → error flash.
- Repo failure → 500 flash.

---

## Task 4 — Project Detail Page

**Branch:** `feature/frontend-task4-project-detail`

### Goal

Implement `GET /projects/{project_id}` — a full detail page for a single project.

### Design Decisions

- `GetProject` use case already existed — no new use case needed.
- `ProjectNotFoundError` (subclass of `DomainException`) maps to HTTP 404.
- All other exceptions map to HTTP 500, reusing `project_not_found.html` with an `unexpected_error` flag for a different message.

### Deliverables

**`GET /projects/{project_id}`** in `routes.py`:
- Calls `GetProject(project_repo=repo).execute(project_id)`.
- Passes to template: `id`, `name`, `status`, `created_at` (formatted `%d %b %Y`), `source_image_ref`, `project_id`.

**`project_detail.html`**:

| Section | Content |
|---|---|
| Breadcrumb | Projects / {name} |
| Header | Project name, project ID (monospace), status badge |
| Source Image | Uploaded ref or "No image uploaded yet." (replaced by partial in Task 5) |
| Actions | Placeholder buttons: Upload Image, Generate Pattern, Export PDF |
| Pattern & Results | Placeholder box |
| Back link | "← Back to Projects" |

**`project_not_found.html`**:
- "Project not found" (404) or "Something went wrong" (500).
- "Back to Projects" button.

### Quality Checks

- Valid project ID → 200, shows name, status badge, date, ID.
- Unknown project ID → 404, friendly page with back link.
- Repo failure → 500, error page.

---

## Task 5 — Upload Source Image (HTMX)

**Branch:** `feature/frontend-task5-upload-source-image`

### Goal

Add a working image upload form to the Source Image card on the project detail page. Upload via HTMX — no page reload. Card updates in-place on success.

### Design Decisions

- **Option A chosen** — upload logic implemented directly in the web route using the same `get_file_storage` + `get_project_repository` dependencies as the JSON API route. No internal HTTP call, no new use case needed.
- The card uses `hx-swap="outerHTML"` on `#source-image-card` so the entire card (including the upload form) is replaced after submission. Users can re-upload without a page reload.
- `file.content_type` is used for MIME validation (set by the browser).

### Deliverables

**`partials/source_image_card.html`** — self-contained card with `id="source-image-card"`:
- Uploaded state: "✓ Image uploaded" + ref in monospace.
- No-image state: "No image uploaded yet."
- Error alert (if `error` is set).
- Upload form: `hx-post="/hx/projects/{{ project_id }}/source-image"`, `hx-target="#source-image-card"`, `hx-swap="outerHTML"`, `hx-encoding="multipart/form-data"`.
- Loading indicator via `htmx-indicator`.

**`project_detail.html`** — updated Source Image section:
```jinja
{% include "partials/source_image_card.html" %}
```

**`POST /hx/projects/{project_id}/source-image`** in `routes.py`:

| Condition | Response |
|---|---|
| Empty filename | `source_image_card.html` (error), HTTP 400 |
| Non-image MIME type | `source_image_card.html` (error), HTTP 400 |
| File > 10 MB | `source_image_card.html` (error), HTTP 400 |
| Project not found | `source_image_card.html` (error), HTTP 404 |
| Success | `source_image_card.html` (updated), HTTP 200 |
| Unexpected error | `source_image_card.html` (error) + structlog, HTTP 500 |

Allowed MIME types: `image/png`, `image/jpeg`, `image/webp`, `image/gif`.

### Quality Checks

- Upload valid PNG/JPEG/WebP → card updates showing "Image uploaded" + ref.
- Upload non-image file → 400, error shown in card.
- Upload to non-existent project → 404, error shown in card.
- Repo failure → 500, error shown in card.
- Detail page still renders normally without JavaScript.

---

## Integration Test Coverage

All web routes are covered by `tests/integration/test_web_routes.py` using FastAPI `TestClient` with SQLite in-memory and dependency overrides — the same pattern as the existing API tests.

| Test class | Routes covered |
|---|---|
| `TestHomePage` | `GET /` |
| `TestProjectsPage` | `GET /projects` |
| `TestProjectsPageForm` | `GET /projects` (form elements) |
| `TestHxProjectsEmpty` | `GET /hx/projects` (empty state) |
| `TestHxProjectsPopulated` | `GET /hx/projects` (with data) |
| `TestHxProjectsError` | `GET /hx/projects` (repo failure) |
| `TestHxCreateProject` | `POST /hx/projects/create` |
| `TestProjectDetailPage` | `GET /projects/{project_id}` |
| `TestHxUploadSourceImage` | `POST /hx/projects/{project_id}/source-image` |
