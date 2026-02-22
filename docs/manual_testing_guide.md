# Manual End-to-End Testing Guide

This guide walks through manually testing every feature of the Cross-Stitch Pattern Generator API. You will need a terminal with **curl** (or PowerShell `Invoke-WebRequest`) and a small test image.

---
## Prerequisites

### 1. Start PostgreSQL via Docker

```bash
docker-compose -f docker/docker-compose.yml up db -d
```

Wait a few seconds for the healthcheck to pass, then verify:

```bash
docker-compose -f docker/docker-compose.yml ps
```

You should see the `db` service as **healthy**.

### 2. Run Alembic Migrations

```powershell
.\.venv\Scripts\Activate.ps1
alembic upgrade head
```

Expected output (all three migrations should appear on a fresh database):

```
INFO  [alembic.runtime.migration] Running upgrade  -> 4d14890bf062, create projects and pattern_results tables
INFO  [alembic.runtime.migration] Running upgrade 4d14890bf062 -> b7e3f1a2c4d5, add source image dimensions to projects
INFO  [alembic.runtime.migration] Running upgrade b7e3f1a2c4d5 -> c1e2f3a4b5d6, add processing_mode and variant to pattern_results
```

On an existing database only the missing migrations will run.

### 3. Start the Application

```powershell
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

You should see:

```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### 4. Prepare a Test Image

Save any small image (PNG or JPG) to a known path, e.g. `C:\tmp\test_image.png`. A simple 100x100 pixel image with a few colours works well. You can create one in Paint or download any small photo.

### 5. Interactive Docs (Alternative to curl)

You can also use the built-in Swagger UI for all requests:

```
http://127.0.0.1:8000/api/docs
```

---

## Test 1: Health Check

**What it tests:** Application is running and responding.

```bash
curl http://127.0.0.1:8000/health
```

**Expected response (200):**

```json
{"status": "healthy", "version": "0.1.0"}
```

---

## Test 2: Calculate Fabric Requirements

**What it tests:** Domain services (fabric size + floss estimation).

```bash
curl -X POST http://127.0.0.1:8000/api/patterns/calculate-fabric ^
  -H "Content-Type: application/json" ^
  -d "{\"pattern_width\": 100, \"pattern_height\": 80, \"aida_count\": 14, \"num_colors\": 8}"
```

**Expected response (200):**

```json
{
  "fabric": {"width_cm": 23.14, "height_cm": 19.51},
  "thread": {"total_stitches": 8000, "num_colors": 8, "skeins_per_color": 2, "total_skeins": 16}
}
```

Verify:
- [x] `fabric.width_cm` and `fabric.height_cm` are positive floats
- [x] `thread.total_stitches` equals `pattern_width * pattern_height` (100 * 80 = 8000)

### Validation test (should fail):

```bash
curl -X POST http://127.0.0.1:8000/api/patterns/calculate-fabric ^
  -H "Content-Type: application/json" ^
  -d "{\"pattern_width\": 0, \"pattern_height\": 80, \"aida_count\": 14, \"num_colors\": 8}"
```

**Expected response (422):** Validation error about `pattern_width`.

---

## Test 3: Convert Image to Pattern

**What it tests:** Image processing pipeline (resize, colour quantisation, DMC matching).

```bash
curl -X POST http://127.0.0.1:8000/api/patterns/convert ^
  -F "file=@C:\tmp\test_image.png" ^
  -F "target_width=20" ^
  -F "target_height=15" ^
  -F "num_colors=5"
```

**Expected response (200):**

```json
{
  "grid": {
    "width": 20,
    "height": 15,
    "cells": [[0, 1, 2, ...], ...]
  },
  "palette": [[255, 0, 0], [0, 128, 64], ...],
  "dmc_colors": [
    {"number": "321", "name": "Red", "r": 199, "g": 43, "b": 59},
    ...
  ]
}
```

Verify:
- [x] `grid.width` = 20 and `grid.height` = 15
- [x] `grid.cells` has exactly 15 rows, each with 20 elements
- [x] All cell values are between 0 and `num_colors - 1`
- [x] `palette` has exactly 5 entries (matching `num_colors`)
- [x] `dmc_colors` has exactly 5 entries with valid DMC numbers and names
- [x] Each palette colour is an `[r, g, b]` array with values 0-255

**Save the response** - you will need `grid`, `palette`, and `dmc_colors` for Test 4.

### Validation test (missing file):

```bash
curl -X POST http://127.0.0.1:8000/api/patterns/convert ^
  -F "target_width=20" ^
  -F "target_height=15" ^
  -F "num_colors=5"
```

**Expected response (422):** Validation error about missing `file`.

---

## Test 4: Export Pattern to PDF

**What it tests:** PDF generation (overview + legend + grid pages).

Use the `grid`, `palette`, and `dmc_colors` from Test 3. Replace the example values below with your actual results.

### Colour variant:

```bash
curl -X POST http://127.0.0.1:8000/api/patterns/export-pdf ^
  -H "Content-Type: application/json" ^
  -d "{\"grid\": {\"width\": 20, \"height\": 15, \"cells\": [[0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1],[0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1],[0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1],[0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1],[0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1],[0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1],[0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1],[0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1],[0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1],[0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1],[0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1],[0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1],[0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1],[0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1],[0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1]]}, \"palette\": [[255,0,0],[0,128,0],[0,0,255]], \"dmc_colors\": [{\"number\":\"321\",\"name\":\"Red\",\"r\":199,\"g\":43,\"b\":59},{\"number\":\"699\",\"name\":\"Green\",\"r\":5,\"g\":101,\"b\":23},{\"number\":\"796\",\"name\":\"Royal Blue\",\"r\":17,\"g\":65,\"b\":109}], \"title\": \"My Test Pattern\", \"variant\": \"color\"}" ^
  -o test_pattern_color.pdf
```

### Black-and-white variant:

```bash
curl -X POST http://127.0.0.1:8000/api/patterns/export-pdf ^
  -H "Content-Type: application/json" ^
  -d "{\"grid\": {\"width\": 20, \"height\": 15, \"cells\": [[0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1],[0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1],[0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1],[0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1],[0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1],[0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1],[0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1],[0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1],[0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1],[0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1],[0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1],[0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1],[0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1],[0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1],[0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1]]}, \"palette\": [[255,0,0],[0,128,0],[0,0,255]], \"dmc_colors\": [{\"number\":\"321\",\"name\":\"Red\",\"r\":199,\"g\":43,\"b\":59},{\"number\":\"699\",\"name\":\"Green\",\"r\":5,\"g\":101,\"b\":23},{\"number\":\"796\",\"name\":\"Royal Blue\",\"r\":17,\"g\":65,\"b\":109}], \"title\": \"My Test Pattern BW\", \"variant\": \"bw\"}" ^
  -o test_pattern_bw.pdf
```

Verify by opening both PDFs:
- [x] **Page 1 (Overview):** Title, stitch dimensions, fabric info, colour preview
- [x] **Page 2 (Legend):** DMC numbers, colour names, stitch counts, skein estimates
- [x] **Page 3+ (Grid):** Pattern grid with symbols; colour variant shows coloured cells, BW variant shows white cells with symbols
- [x] Grid has centre lines (dashed) marking the middle of the pattern
- [x] Row and column numbers along the edges

---

## Test 5: Create a Project (Persistence)

**What it tests:** POST endpoint, UUID generation, PostgreSQL insert.

```bash
curl -X POST http://127.0.0.1:8000/api/projects ^
  -H "Content-Type: application/json" ^
  -d "{\"name\": \"Landscape Sunset\", \"parameters\": {\"num_colors\": 12, \"aida_count\": 14}}"
```

**Expected response (201):**

```json
{
  "id": "some-uuid-here",
  "name": "Landscape Sunset",
  "created_at": "2026-02-09T...",
  "status": "created",
  "source_image_ref": null,
  "parameters": {"num_colors": 12, "aida_count": 14}
}
```

**Save the `id`** value for subsequent tests. We'll refer to it as `$PROJECT_ID`.

Verify:
- [x] Status code is 201
- [x] `id` is a valid UUID
- [x] `status` is `"created"`
- [x] `parameters` matches what was sent (JSON roundtrip)

### Validation test (empty name):

```bash
curl -X POST http://127.0.0.1:8000/api/projects ^
  -H "Content-Type: application/json" ^
  -d "{\"name\": \"\"}"
```

**Expected response (422).**

---

## Test 6: List Projects

**What it tests:** GET list endpoint, PostgreSQL query.

```bash
curl http://127.0.0.1:8000/api/projects
```

**Expected response (200):**

```json
[
  {
    "id": "...",
    "name": "Landscape Sunset",
    "status": "created",
    ...
  }
]
```

Verify:
- [x] Returns an array containing the project created in Test 5

---

## Test 7: Get Project by ID

**What it tests:** GET by ID endpoint, single-record query.

```bash
curl http://127.0.0.1:8000/api/projects/$PROJECT_ID
```

Replace `$PROJECT_ID` with the UUID from Test 5.

**Expected response (200):** Same project data as Test 5.

### Not found test:

```bash
curl http://127.0.0.1:8000/api/projects/nonexistent-id
```

**Expected response (400):**

```json
{"detail": "Project not found: nonexistent-id"}
```

---

## Test 8: Update Project Status

**What it tests:** PATCH endpoint, status transitions, PostgreSQL update.

```bash
curl -X PATCH http://127.0.0.1:8000/api/projects/$PROJECT_ID/status ^
  -H "Content-Type: application/json" ^
  -d "{\"status\": \"in_progress\"}"
```

**Expected response:** 204 No Content (empty body).

Then verify the change persisted:

```bash
curl http://127.0.0.1:8000/api/projects/$PROJECT_ID
```

- [x] `status` is now `"in_progress"`
- [x] All other fields (`name`, `parameters`, etc.) are unchanged

### Test all valid transitions:

Repeat with `"completed"` and `"failed"` to confirm all statuses work.

### Validation test (invalid status):

```bash
curl -X PATCH http://127.0.0.1:8000/api/projects/$PROJECT_ID/status ^
  -H "Content-Type: application/json" ^
  -d "{\"status\": \"invalid_status\"}"
```

**Expected response (422).**

---

## Test 9: Save a Pattern Result

**What it tests:** Pattern result creation, foreign key to project, JSONB persistence.

```bash
curl -X POST http://127.0.0.1:8000/api/projects/$PROJECT_ID/patterns ^
  -H "Content-Type: application/json" ^
  -d "{\"palette\": {\"colors\": [{\"number\": \"321\", \"name\": \"Red\", \"r\": 199, \"g\": 43, \"b\": 59}, {\"number\": \"699\", \"name\": \"Green\", \"r\": 5, \"g\": 101, \"b\": 23}]}, \"grid_width\": 100, \"grid_height\": 80, \"stitch_count\": 8000, \"pdf_ref\": \"projects/abc/pattern.pdf\"}"
```

**Expected response (201):**

```json
{
  "id": "some-uuid",
  "project_id": "$PROJECT_ID",
  "created_at": "2026-02-09T...",
  "palette": {"colors": [...]},
  "grid_width": 100,
  "grid_height": 80,
  "stitch_count": 8000,
  "pdf_ref": "projects/abc/pattern.pdf",
  "processing_mode": "auto",
  "variant": "color"
}
```

Verify:
- [x] `project_id` matches the project from Test 5
- [x] `palette` JSON was stored and returned correctly
- [x] `grid_width`, `grid_height`, `stitch_count` match input
- [x] `processing_mode` and `variant` are present and reflect what was sent

### Foreign key test (non-existent project):

```bash
curl -X POST http://127.0.0.1:8000/api/projects/nonexistent-id/patterns ^
  -H "Content-Type: application/json" ^
  -d "{\"palette\": {}, \"grid_width\": 10, \"grid_height\": 10, \"stitch_count\": 100}"
```

**Expected response (400):** Project not found error.

---

## Test 10: Full End-to-End Workflow

This combines all features into a realistic user flow.

### Step 1 - Create a project

```bash
curl -X POST http://127.0.0.1:8000/api/projects ^
  -H "Content-Type: application/json" ^
  -d "{\"name\": \"My Cross-Stitch\", \"parameters\": {\"num_colors\": 5, \"aida_count\": 14}}"
```

Note the `id` from the response.

### Step 2 - Update status to in_progress

```bash
curl -X PATCH http://127.0.0.1:8000/api/projects/$PROJECT_ID/status ^
  -H "Content-Type: application/json" ^
  -d "{\"status\": \"in_progress\"}"
```

### Step 3 - Convert an image

```bash
curl -X POST http://127.0.0.1:8000/api/patterns/convert ^
  -F "file=@C:\tmp\test_image.png" ^
  -F "target_width=40" ^
  -F "target_height=30" ^
  -F "num_colors=5" ^
  -o convert_response.json
```

### Step 4 - Calculate fabric requirements

```bash
curl -X POST http://127.0.0.1:8000/api/patterns/calculate-fabric ^
  -H "Content-Type: application/json" ^
  -d "{\"pattern_width\": 40, \"pattern_height\": 30, \"aida_count\": 14, \"num_colors\": 5}"
```

### Step 5 - Export to PDF

Build the export-pdf body from the convert response (grid, palette, dmc_colors) and call:

```bash
curl -X POST http://127.0.0.1:8000/api/patterns/export-pdf ^
  -H "Content-Type: application/json" ^
  -d "<JSON body with grid, palette, dmc_colors, title, variant>" ^
  -o my_pattern.pdf
```

Open `my_pattern.pdf` and visually inspect all pages.

### Step 6 - Save pattern result to the project

```bash
curl -X POST http://127.0.0.1:8000/api/projects/$PROJECT_ID/patterns ^
  -H "Content-Type: application/json" ^
  -d "{\"palette\": <palette from convert>, \"grid_width\": 40, \"grid_height\": 30, \"stitch_count\": 1200, \"pdf_ref\": \"my_pattern.pdf\"}"
```

### Step 7 - Mark project as completed

```bash
curl -X PATCH http://127.0.0.1:8000/api/projects/$PROJECT_ID/status ^
  -H "Content-Type: application/json" ^
  -d "{\"status\": \"completed\"}"
```

### Step 8 - Verify everything persisted

```bash
curl http://127.0.0.1:8000/api/projects/$PROJECT_ID
```

- [x] Status is `"completed"`
- [x] All project fields intact

---

## Test 11: Database Persistence Verification

Restart the server to confirm data survives restarts (since PostgreSQL is the backing store):

1. Stop uvicorn (`Ctrl+C`)
2. Start it again: `uvicorn app.main:app --reload`
3. List projects:

```bash
curl http://127.0.0.1:8000/api/projects
```

- [x] All previously created projects and pattern results are still present

---

## Test 12: Swagger UI Walkthrough

Visit `http://127.0.0.1:8000/api/docs` in a browser and:

- [x] All endpoints are listed with descriptions
- [x] "Try it out" works for each endpoint
- [x] Request/response schemas are shown
- [x] File upload works for the convert endpoint

---

## Cleanup

```bash
# Stop the application (Ctrl+C in the uvicorn terminal)

# Stop and remove the database container + data
docker-compose -f docker/docker-compose.yml down -v
```

---

## Quick Reference: All Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/api/patterns/calculate-fabric` | Calculate fabric and thread requirements |
| POST | `/api/patterns/convert` | Convert image to cross-stitch pattern |
| POST | `/api/patterns/export-pdf` | Export pattern as PDF |
| POST | `/api/projects` | Create a new project |
| GET | `/api/projects` | List all projects |
| GET | `/api/projects/{id}` | Get project by ID |
| PATCH | `/api/projects/{id}/status` | Update project status |
| POST | `/api/projects/{id}/patterns` | Save a pattern result to a project |
