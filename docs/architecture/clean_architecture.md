# Clean Architecture Diagram

This diagram shows the layered architecture of the Cross-Stitch Pattern Generator application.

```mermaid
graph TD
    A[Web Layer - FastAPI] --> B[Application Layer - Use Cases]
    B --> C[Domain Layer - Entities & Services]
    B --> D[Infrastructure Layer - Adapters]
    D --> E[(PostgreSQL)]
    D --> F[Image Processing]
    D --> G[PDF Export]
```

## Layer Responsibilities

- **Web Layer**: FastAPI routes, request/response handling, HTTP concerns
- **Application Layer**: Use cases that orchestrate domain logic and infrastructure
- **Domain Layer**: Core business entities, services, and repository interfaces (framework-independent)
- **Infrastructure Layer**: Concrete implementations of external dependencies (database, file system, external APIs)