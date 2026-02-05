```mermaid
graph TD
     A[Web Layer - FastAPI] --> B[Application Layer - Use Cases]
     B --> C[Domain Layer - Entities & Services]
     B --> D[Infrastructure Layer - Adapters]
     D --> E[(PostgreSQL)]
     D --> F[Image Processing]
     D --> G[PDF Export]