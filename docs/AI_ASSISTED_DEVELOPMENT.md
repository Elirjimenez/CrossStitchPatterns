# AI-Assisted Development Traceability

This document fulfils the TFM requirement to describe how AI tools were used responsibly  
during the development of the **Cross-Stitch Pattern Generator**, following a strict  
**Human-in-the-Loop engineering methodology**.

---

## 1. Overview

The Cross-Stitch Pattern Generator was **conceived, designed, and architected by the human developer**.

AI tools (Claude Code and ChatGPT) were employed strictly as **technical assistants** supporting the development workflow. Their role was limited to generating code proposals, suggesting test cases, and discussing alternative implementations.

All core responsibilities remained under human control:

- Feature definition and prioritisation  
- System architecture and design decisions  
- Technology selection  
- Code review and validation  
- Test execution  
- Version control and commits  

The AI did not operate autonomously at any stage.

---

## 2. Development Methodology

Every development cycle followed a **human-driven workflow**:
1. Human defines feature scope, requirements, and acceptance criteria
2. AI assists by proposing implementation alternatives
3. Human evaluates trade-offs and selects the preferred approach
4. AI generates code consistent with human decisions
5. Human reviews, edits, and validates the implementation
6. Human executes tests and verifies behaviour
7. Human performs commits and repository management

This structure ensured that:

✔ Engineering intent originated from the human developer  
✔ AI output remained bounded by explicit instructions  
✔ No code entered the repository without human validation

---

## 3. Tools Used

| Tool | Role |
|------|------|
| **Claude Code (claude-sonnet-4-6)** | Assisted with code drafting, TDD cycles, refactoring suggestions |
| **ChatGPT** | Assisted with planning discussions, design exploration, documentation refinement |

AI tools functioned as **advanced development aids**, analogous to pair programming rather than autonomous agents.

---

## 4. Human-Led System Design

The human developer was responsible for:

- Defining the product concept (image → cross-stitch pattern system)
- Selecting the Clean Architecture approach
- Designing domain boundaries and dependency rules
- Choosing technologies (FastAPI, SQLAlchemy, ReportLab, HTMX, etc.)
- Establishing generation constraints and UX principles
- Determining validation rules and safety limits
- Deciding algorithmic strategies (e.g., deterministic image heuristics)

AI tools assisted in **implementing**, not **originating**, these decisions.

---

## 5. AI-Assisted Contributions

### 5.1 Test-Driven Development Support

The human developer adopted TDD as the governing methodology.  
AI assistance was used to accelerate mechanical aspects of the cycle:

- Drafting initial failing tests based on human-defined behaviour
- Generating minimal production code proposals
- Suggesting refactoring patterns

All tests, behaviours, and edge cases were defined and validated by the human developer.

---

### 5.2 Implementation Assistance

AI tools supported implementation tasks such as:

- Translating human-defined logic into code structures
- Proposing alternative refactoring approaches
- Generating boilerplate adapters (repositories, PDF exporter, etc.)

The human developer retained responsibility for:

✔ Reviewing correctness  
✔ Adjusting logic  
✔ Rejecting unsuitable proposals  
✔ Ensuring architectural consistency

---

### 5.3 Architecture Consistency Checks

AI tools were used as a **secondary validation mechanism**:

- Highlighting potential Clean Architecture violations
- Suggesting interface/port abstractions
- Discussing design trade-offs

Final architectural decisions were always human-driven.

---

### 5.4 Image Mode Detection Feature

The **feature concept, rationale, and design strategy** were defined by the human developer:

- Identifying the need for deterministic image classification
- Choosing a heuristic rather than ML-based approach
- Defining constraints (no training dataset, predictable runtime)

AI assistance was used only to:

✔ Draft code consistent with the chosen design  
✔ Generate test scaffolding  

Thresholds, signals, and validation were decided through human judgement and empirical testing.

---

## 6. What the AI Did NOT Do

- **No autonomous decision-making**
- **No independent architecture design**
- **No unreviewed code integration**
- **No repository management**
- **No dependency selection**

AI tools did not introduce features, technologies, or design changes without explicit human direction.

---

## 7. Human Oversight & Control Mechanisms

| Control Area | Enforcement |
|--------------|-------------|
| Feature scope | Defined exclusively by human developer |
| Architecture | Governed by human-approved design rules |
| Dependencies | Added only after human evaluation |
| Code quality | Human review + automated tests |
| Validation & security | Human inspection of all file & input logic |
| Version control | Human commits only |

---

## 8. Traceability by Feature

| Feature | Primary Driver | AI Role |
|---------|---------------|---------|
| Domain model & architecture | Human | Assisted with structural drafting |
| Fabric size calculator | Human | Assisted with TDD scaffolding |
| PDF export system | Human (tech selection) | Assisted with adapter code |
| Persistence layer | Human (design decisions) | Assisted with ORM boilerplate |
| Project management flows | Human | Assisted with implementation |
| Frontend HTMX flows | Human (UX logic) | Assisted with code drafting |
| Generation safety limits | Human | Assisted with validator implementation |
| Image mode detection | Human (concept & design) | Assisted with code & tests |
| Delete project logic | Human | Assisted with implementation |

---

## 9. Lessons Learned

1. **AI is most effective as an accelerator, not a decision-maker**  
   Engineering quality depends on human architectural control.

2. **TDD provides a safety net for AI-generated code**  
   Behaviour is validated rather than assumed correct.

3. **Human judgement remains critical**  
   Especially for UX, constraints, thresholds, and trade-offs.

4. **Incremental commits enable full traceability**  
   Each feature reflects human intent with auditable history.