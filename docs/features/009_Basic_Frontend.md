Context
- Backend is FastAPI with existing API endpoints under /api (projects, patterns, etc.).
- We want a very simple server-rendered frontend using:
  - FastAPI for routing
  - Jinja2 templates for HTML
  - HTMX for interactivity
  - Tailwind via CDN (no build step)
- Keep it minimal, pragmatic, and consistent with a “Clean Architecture (light)” repo. Don’t refactor business logic.
- Goal of Task 1: I can run the app and see a styled HTML page rendered by Jinja2.

Constraints
- No JavaScript framework (no React/Vue).
- Tailwind must be CDN-based (no npm, no build pipeline).
- HTMX must be included via CDN (even if not used yet).
- Create clean file structure and wire it into FastAPI app startup.
- Prefer explicit, readable code over clever abstractions.

Deliverables (Task 1)
1) File structure
- Create (or update) a frontend module under something like:
  app/web/
    __init__.py
    routes.py              # HTML routes (FastAPI APIRouter)
    templates/
      base.html
      home.html
    static/
      css/ (optional)
      img/ (optional)
- If the project uses a different structure already, adapt respectfully (don’t break imports).

2) Jinja2 setup
- Configure Jinja2Templates and mount StaticFiles in the FastAPI app (app/main.py or equivalent).
- Ensure templates resolve correctly.

3) HTML routes
- Add a simple “Home” page route, e.g. GET /
- Add a simple “Projects” placeholder route, e.g. GET /projects
  (For now this can render a placeholder page; real functionality comes later.)

4) Base layout
- base.html includes:
  - Tailwind CDN
  - HTMX CDN
  - A minimal navbar with links: Home, Projects
  - A main container block for page content
- home.html extends base.html and shows:
  - Title: “Cross-Stitch Pattern Generator”
  - Short subtitle and 1–2 call-to-action buttons (e.g. “View Projects”)
- projects.html (optional now) can just show “Projects (coming next)”.

5) Quality checks
- App should start without errors.
- Visiting / renders the home page.
- Visiting /projects renders placeholder.

Implementation notes
- Use FastAPI APIRouter for web routes.
- Keep naming consistent: “web routes” vs “api routes”.
- Do not change existing /api endpoints.
- If you need a settings/config object, keep it minimal and do not introduce heavy dependencies.

Output format
- Provide the exact code diffs or full file contents for each created/modified file.
- Also include a short “How to run” section (commands + URLs).
