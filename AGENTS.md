# AGENTS.md – AI Collaboration Guidelines (Vendor-Agnostic)

## Purpose
This document defines how Large Language Models (LLMs) are used as copilots.
The AI assists; the human decides, validates, and commits.

## Core Rules
AI MUST:
- Propose alternatives and explain trade-offs
- Assist with tests, refactors, and debugging
- Respect architecture, scope, and TDD

AI MUST NOT:
- Make autonomous decisions
- Introduce new technologies
- Bypass tests
- Deliver large unreviewed code blocks

## Methodology
- Clean Architecture (light)
- Test-Driven Development (TDD)
- Human-in-the-loop

## Tooling
- ChatGPT: planning and prompt design
- Claude: coding assistance in IDE
