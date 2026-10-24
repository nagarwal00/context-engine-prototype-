# AI Assistance Disclosure

> **Academic Integrity Notice:** Check UCS503 policy on AI tool use. This disclosure records the use of AI tools during the development of the Context Intelligence Framework (CIF) in accordance with academic integrity guidelines and capstone evaluation requirements.

---

## 1. Overview & Tool Identification

- **Tools Used:** Antigravity IDE / Agentic Coding Assistant (Google DeepMind Advanced Agentic Coding).
- **Model Family:** Gemini Advanced Reasoning / Coding Models.
- **Role of AI:** Pair programming and autonomous implementation agent executing structured instructions defined in engineering specifications.

---

## 2. Scope of AI Assistance

The AI coding agent was used strictly for execution of explicit specifications:
1. **Implementation from Specifications:** Implementing modules from written design documents ([`docs/process/implementation.md`](docs/process/implementation.md) and [`docs/process/ANTIGRAVITY_HANDOFF_V4_FIXES.md`](docs/process/ANTIGRAVITY_HANDOFF_V4_FIXES.md)), including data models, database migration scripts, ingestion adapters, graph query helpers, and reconciliation logic.
2. **Test Suite Expansion:** Writing automated unit and regression tests in [`tests/`](tests/) matching test specifications.
3. **Tooling & Benchmark Scripts:** Writing verification scripts, fact printers, and baseline evaluators in [`tools/`](tools/).
4. **Documentation Synchronization:** Aligning markdown documentation with live codebase counts and moving presenter notes.

---

## 3. Author Responsibilities & Independent Contributions

*In accordance with Capstone Project requirements, the human author(s) maintain sole responsibility for the project architecture, design choices, validation, and oral defense. All student contributions are documented below:*

### 3.1 System Architecture & Design Decisions
- `TODO(human)`: [Specify design decisions, architectural trade-offs, and data model schemas designed independently by the author(s)].
- `TODO(human)`: [Specify rationale for selecting SQLite, standard-library-only constraints, and the mechanical evidence invariant].

### 3.2 Human Review & Code Inspection
- `TODO(human)`: [Detail which generated modules, pull requests, and migrations were reviewed, verified, or debugged by the human author(s)].
- `TODO(human)`: [Describe any human corrections made to fix edge cases or alignment with course requirements].

### 3.3 Conceptual Mastery & Examination Readiness
- `TODO(human)`: [List the core modules and algorithms the author(s) are prepared to defend and explain in oral examination (e.g., AST visitor mechanics in `entity_res.py`, temporal graph query resolution, word-boundary conflict detection, guard-rule synthesis)].

---

## 4. Pending Human Verification Tasks

The following empirical evaluations require human execution per [`docs/process/ANTIGRAVITY_HANDOFF_V4_FIXES.md`](docs/process/ANTIGRAVITY_HANDOFF_V4_FIXES.md) §12:
- **H-1:** Build a genuinely real open-source corpus (`WhyBench-Real`).
- **H-2:** Execute Baseline C (Plain LLM) using real API credentials (`CIF_LLM_API_KEY`).
- **H-3:** Fill manual Copilot evaluation sheet (`results/copilot_sheet.md`).
- **H-4:** Annotate precision labelling sample (`results/precision_sheet.csv`).
- **H-5:** Conduct human user study across 5–8 participants (`user_study/PROTOCOL.md`).
- **H-6:** Complete all `TODO(human)` placeholders in this document and `CONTRIBUTIONS.md`.
