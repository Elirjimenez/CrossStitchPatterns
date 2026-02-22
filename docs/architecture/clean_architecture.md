# Clean Architecture

## Dependency Rule

The fundamental constraint of Clean Architecture: **dependencies only point inward**.
The Domain layer has zero dependencies on any outer layer — it is pure Python.

```
┌─────────────────────────────────────────┐
│              Web  /  Infrastructure     │  ← depends on Application
│  ┌───────────────────────────────────┐  │
│  │           Application             │  │  ← depends on Domain
│  │  ┌─────────────────────────────┐  │  │
│  │  │          Domain             │  │  │  ← depends on NOTHING
│  │  │  (entities, services, ports)│  │  │
│  │  └─────────────────────────────┘  │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

Arrows show allowed import directions:

```mermaid
graph LR
    W[Web] --> A[Application]
    I[Infrastructure] --> A
    A --> D[Domain]

    style D fill:#d4edda,stroke:#28a745,color:#000
    style A fill:#d1ecf1,stroke:#17a2b8,color:#000
    style W fill:#fff3cd,stroke:#ffc107,color:#000
    style I fill:#fff3cd,stroke:#ffc107,color:#000
```

**Domain never imports from Application, Infrastructure, or Web.**
Ports (interfaces) defined in Application allow Infrastructure to plug in without
the Domain knowing anything about databases, HTTP, or file systems.

---

## Runtime Data Flow

How a request travels through the layers at runtime:

```mermaid
graph TD
    A[Web Layer - FastAPI] --> B[Application Layer - Use Cases]
    B --> C[Domain Layer - Entities & Services]
    B --> D[Infrastructure Layer - Adapters]
    D --> E[(PostgreSQL)]
    D --> F[Image Processing]
    D --> G[PDF Export]
```

---

## Layer Responsibilities

| Layer | Package | Responsibility |
|---|---|---|
| **Domain** | `app/domain/` | Business rules, entities, repository interfaces — framework-independent |
| **Application** | `app/application/` | Use cases, ports (Protocols), workflow orchestration |
| **Infrastructure** | `app/infrastructure/` | SQLAlchemy, Pillow, ReportLab, local file storage |
| **Web** | `app/web/` | FastAPI routes, HTMX partials, HTTP request/response |