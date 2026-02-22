# Reviewer Guide — Cross-Stitch Pattern Generator

This guide is intended for TFM reviewers and panel members who wish to
explore the live application. Eight demo projects have been pre-generated
and are ready to browse, download, and inspect.

---

## Live Application

| Resource | URL |
|---|---|
| Web UI | https://crossstitchpatterns-production.up.railway.app |
| Projects list | https://crossstitchpatterns-production.up.railway.app/projects |
| API Documentation | https://crossstitchpatterns-production.up.railway.app/api/docs |
| Health check | https://crossstitchpatterns-production.up.railway.app/health |

> The application is hosted on Railway's free tier. If the instance is
> sleeping, allow 10–15 seconds on the first request for it to wake up.

---

## Pre-Generated Demo Projects

Eight projects have been generated from a curated image bank to showcase
the full range of the system's capabilities. Each can be opened from the
Projects list page.

| # | Project Name | Size (stitches) | Colours | Variant | Showcases |
|---|---|---|---|---|---|
| 1 | Pixel Art Character – Colour | 80 × 80 | 8 | Colour | Pixel art mode; resized from 256 × 256 source |
| 2 | Heart – B&W | 60 × 60 | 4 | B&W | Black & White variant; resized from 256 × 256 source |
| 3 | Rainbow Cupcake – Rich Colour | 150 × 150 | 14 | Colour | Drawing mode, multi-page PDF; resized from 300 × 300 source |
| 4 | Cartoon Cat – Drawing | 120 × 120 | 7 | Colour | Cartoon/drawing mode; resized from 300 × 300 source |
| 5 | Photo – High Detail | 250 × 150 | 20 | Colour | Photo mode, max palette, largest PDF; matches 300 × 200 source aspect ratio |
| 6 | Grayscale Portrait – B&W | 150 × 150 | 8 | B&W | B&W portrait — classic cross-stitch use case |
| 7 | Flower – Auto Mode | 100 × 100 | 11 | Colour | Auto image mode detection; resized from 200 × 200 source |
| 8 | Dog Silhouette – Minimal | 80 × 80 | 3 | Colour | Extreme colour reduction (3 DMC threads); resized from 150 × 150 source |

### What each project PDF contains

Every downloaded PDF is a **multi-page document** structured as:
- **Page 1 — Overview**: full pattern at a glance with colour legend
- **Page 2 — Legend**: DMC thread numbers, names, stitch counts, and fabric estimation
- **Page 3+  — Grid pages**: tiled A4 pages of the stitching grid with symbol keys

---

## Suggested Review Path

### 1. Browse existing projects
Open the **Projects** page and click into any project to see:
- The uploaded source image
- Pattern generation parameters
- Results summary (size, stitch count, colours, type)
- Download PDF button

### 2. Download and inspect a PDF
Recommended projects for inspecting the PDF output:
- **Project 5 (Photo – High Detail)** — largest PDF, most grid pages, 20 DMC colours
- **Project 3 (Rainbow Cupcake)** — good balance of colour and page count
- **Project 2 (Heart – B&W)** — simplest PDF, easiest to read in full

### 3. Generate a new pattern yourself
To run the full workflow from scratch:
1. Go to **Projects → New Project**
2. Enter a name and click **Create**
3. Upload any image (PNG or JPEG, up to 10 MB)
4. Set parameters (colours, size, image type, pattern type)
5. Click **Generate Pattern + PDF**
6. Download the resulting PDF

### 4. Explore the API
The interactive API documentation at `/api/docs` (Swagger UI) allows
you to call any endpoint directly from the browser:
- `POST /api/projects/complete` — full workflow in one call
- `GET /api/projects` — list all projects
- `GET /api/projects/{id}` — inspect a specific project
- `POST /api/patterns/convert` — convert an image without saving

---

## Key Technical Points to Observe

| Aspect | Where to look |
|---|---|
| DMC colour matching (CIE Lab Delta E) | PDF legend — thread numbers and names |
| Fabric size estimation | PDF legend — fabric dimensions in cm |
| Floss usage estimation | PDF legend — metres per colour |
| Multi-page tiling | PDF grid pages (most visible in Projects 3 and 5) |
| B&W variant | Projects 2 and 6 |
| Colour reduction quality | Compare Project 8 (3 colours) vs Project 5 (20 colours) |
| Image mode detection | Project 7 (auto mode selects the best processing pipeline) |
| Image resizing | All projects — source images are resized to the requested stitch dimensions; the UI pre-fills width/height from the uploaded image but accepts any user-defined target size |

---

## Repository

The full source code, architecture documentation, and test suite are
available at:

**https://github.com/Elirjimenez/CrossStitchPatterns**
