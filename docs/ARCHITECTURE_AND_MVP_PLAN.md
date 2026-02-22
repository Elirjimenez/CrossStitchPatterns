# Architecture and MVP Plan

## Architecture
- Monolithic modular application
- Clean Architecture principles (light)
- Domain independent from frameworks and database

## MVP Scope
- Image to cross-stitch pattern conversion
- Fabric size calculation
- Floss estimation
- PDF export
- PostgreSQL persistence

## Technology Stack
- FastAPI + HTMX
- PostgreSQL
- Docker
- Pytest (TDD)

## Architectural Rationale

The Clean Architecture approach was selected to:

✔ Ensure separation of concerns  
✔ Preserve domain independence  
✔ Facilitate deterministic testing  
✔ Improve long-term maintainability  

## Scope Control

The MVP scope prioritised:

✔ End-to-end functional completeness  
✔ Architectural correctness  
✔ Engineering quality (TDD)  

Over feature expansion or premature optimisation.
