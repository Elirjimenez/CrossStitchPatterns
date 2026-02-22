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

Most projects use the **source image's native pixel dimensions** as stitch
dimensions (1 pixel = 1 stitch), producing the highest-fidelity pattern
possible. Project 8 deliberately uses a smaller target to demonstrate the
explicit resizing feature.

| # | Project Name | Source | Stitches | Colours req. / actual | Variant | Mode | Aida | Margin | Showcases |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Pixel Art Character – Colour | 256 × 256 px | 256 × 256 | 8 / **8** | Colour | pixel_art | 18 | 3 cm | Fine 18-count Aida for sharp pixel-art detail; compact 3 cm margin |
| 2 | Heart – B&W | 256 × 256 px | 256 × 256 | 4 / **3** | B&W | drawing | 14 | 5 cm | B&W variant; palette capped to 3 (only 3 distinct tone regions) |
| 3 | Rainbow Cupcake – Rich Colour | 300 × 300 px | 300 × 300 | 14 / **14** | Colour | drawing | 11 | 7 cm | Coarse 11-count Aida for display piece; wide 7 cm margin; 90 000 stitches |
| 4 | Cartoon Cat – Drawing | 300 × 300 px | 300 × 300 | 7 / **5** | Colour | drawing | 16 | 4 cm | Medium-fine 16-count; palette capped to 5 distinct colour regions |
| 5 | Photo – High Detail | 300 × 200 px | 300 × 200 | 20 / **20** | Colour | photo | 14 | 5 cm | Photo mode; maximum 20-colour palette; largest PDF; 60 000 stitches |
| 6 | Grayscale Portrait – B&W | 300 × 300 px | 300 × 300 | 8 / **8** | B&W | photo | 18 | 3 cm | Fine 18-count Aida for portrait detail; minimal 3 cm margin |
| 7 | Flower – Auto Mode | 200 × 200 px | 200 × 200 | 11 / **8** | Colour | auto | 20 | 5 cm | Finest 20-count Aida for delicate floral; auto mode detection |
| 8 | Dog Silhouette – Resized | 150 × 150 px | **80 × 80** | 10 / **2** | Colour | drawing | 11 | 8 cm | Explicit downscale (150 → 80 px); coarse 11-count + generous 8 cm margin |

### Expected output for each project

| # | What to look for in the PDF |
|---|---|
| 1 | Clean pixel grid with 8 distinct DMC thread squares; pixel art character recognisable at any zoom level; legend fabric size calculated at 18 Aida (smaller fabric per stitch) |
| 2 | High-contrast heart on a white background using only 3 DMC shades; standard 14-count fabric size in the legend |
| 3 | Richly coloured cupcake; 14 DMC threads in the legend; 3+ grid pages due to 300 × 300 stitch count; fabric size calculated with 11-count Aida and wide 7 cm margin |
| 4 | Cartoon cat with clean outlines; only 5 threads despite requesting 7 — system removed duplicates automatically; 16-count gives medium-fine fabric dimensions |
| 5 | Photographic detail with full 20-colour DMC palette; largest PDF with most grid pages; fabric ~54 × 36 cm at 14 Aida with 5 cm margin |
| 6 | Grayscale portrait rendered in 8 DMC near-black/grey threads; compact fabric size due to fine 18-count Aida |
| 7 | Flower with 8 DMC colours; auto mode selected drawing pipeline; 20-count gives the smallest fabric size of all projects |
| 8 | Small 80 × 80 grid (compare to 150 × 150 source); only 2 DMC threads despite requesting 10; generous 8 cm margin + coarse 11-count Aida shown in legend |

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
4. Set parameters (colours, size, image type, pattern type, Aida count, margin)
5. Click **Generate Pattern + PDF**
6. Download the resulting PDF
7. Navigate away and return to the project — all parameters including Aida count and margin are restored in the Actions panel

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
| Image resizing | Project 8 — source is 150 × 150 px, pattern is 80 × 80 stitches; all other projects use native dimensions (1 px = 1 stitch) |
| Automatic palette capping | Projects 2, 4, 7, 8 — requested colour count exceeds the number of distinct colour regions in the image; system caps the palette automatically so no empty or duplicate DMC threads appear in the legend |
| Settings persistence across navigation | Open any completed project, note the Image type, Pattern type, Aida count, Margin, number of colours, and target size in the Actions panel — all reflect the values used for the last generation, not the defaults. The Results card also displays Image mode, Aida count, and Margin. All values are stored in the database alongside the pattern result. |
| Varied Aida count and margin per project | Each demo project uses a different Aida count (11, 14, 16, 18, or 20) and margin (3–8 cm). Observe how fabric size in each PDF legend changes accordingly. |

---

## Repository

The full source code, architecture documentation, and test suite are
available at:

**https://github.com/Elirjimenez/CrossStitchPatterns**
