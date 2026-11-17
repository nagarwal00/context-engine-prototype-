# Context Engine — Live Demonstration & Oral Examination Guide

**Audience**: Project Evaluator / Examination Committee / Course Instructor  
**System**: Context Intelligence Framework (CIF)  
**Presenter**: Student Project Team  
**Estimated Presentation Time**: 10–15 Minutes  

---

## 1. Opening Pitch (1 Minute)

> *"Good morning, Professor. Today we present **Context Engine**, a context intelligence framework that solves one of software engineering's most expensive problems: **knowledge loss and architectural drift**.*
>
> *When engineers leave a team or new developers onboard, they understand **what** the code does by reading it, but they don't know **why** it was written that way—or what was tried and rejected in the past. This leads to repeating previously failed approaches, violating implicit constraints, and introducing costly architectural regressions.*
>
> *Context Engine captures, links, and grounds architectural decisions directly into code entities using AST parsing and Git provenance, backed by a mathematical invariant that prevents AI hallucination."*

---

## 2. Walkthrough Scenarios

### Scenario 1: Decision Traceability (Code ➔ Decision ➔ ADR ➔ Commit)
1. **Action**: Open the dashboard (`http://127.0.0.1:8080/dashboard.html` or deployed GitHub Pages link).
2. **Action**: In the top navigation, click on **Code Context**.
3. **Highlight to Professor**:
   - Point to `src/thermal/control.py::regulate_temperature`.
   - Explain how the Python AST parser extracted the exact function signature without running arbitrary code.
   - Click **"Inspect code context"** or the decision badge.
   - Show the **Evidence Panel**: demonstrate that this decision is backed by *ADR 0004* and commit `a1b2c3d` with direct clickable citations.
4. **Key Talking Point**:
   > *"Every decision in our system satisfies our **Mechanical Invariant**: an accepted decision cannot exist without at least one verifiable, clickable provenance link to a real Git event or ADR."*

---

### Scenario 2: Interactive Context Graph Visualizer
1. **Action**: Click on **Context Graph** in the top navigation.
2. **Highlight to Professor**:
   - Show how nodes represent Decisions, Code Entities (files/functions), and Evidence Events.
   - Toggle edge filters (e.g., filter by `conflicts_with` or `drifts_from`).
   - Drag nodes to show dynamic force layout.
3. **Key Talking Point**:
   > *"Engineers can visualize how an architectural decision ripples through multiple files across the repository, identifying shared dependencies and potential conflict hotspots."*

---

### Scenario 3: Real-Time Drift Detection & Rejected Idea Interception
1. **Action**: Click on **Review Queue** or navigate to the PR Guard test.
2. **Action**: Demonstrate entering a proposed code diff that reintroduces a bang-bang controller (an approach previously rejected in ADR 0004 due to thermal overshoots).
3. **Highlight to Professor**:
   - The engine flags the PR as an **advisory warning**, citing the exact historical decision, author, date, and benchmark overshoot evidence.
   - Emphasize that it is **advisory** rather than an auto-blocker, respecting human developer agency while preventing zombie ideas.
4. **Key Talking Point**:
   > *"Notice how Context Engine doesn't just check lint rules—it checks organizational memory to stop teams from repeating mistakes made months ago."*

---

### Scenario 4: Historical Time-Travel (`as-of` Query)
1. **Action**: Open the **Timeline** view.
2. **Action**: Adjust the date filter to an earlier date (e.g., `2026-01-14`).
3. **Highlight to Professor**:
   - Observe that the PID controller decision vanishes or appears in its earlier `proposed` state, because it was only accepted on `2026-01-15`.
4. **Key Talking Point**:
   > *"By querying the temporal graph with `as-of` cuts, developers and auditors can reconstruct the exact state of knowledge that existed when a specific commit was authored, preventing hindsight bias."*

---

### Scenario 5: Real Repository Ingestion
1. **Action**: Open the **Workspace** menu in the top right.
2. **Action**: Enter the real repository URL:
   `https://github.com/nagarwal00/breathwise-innovation-hackathon`
3. **Action**: Click **Ingest Repository**.
4. **Highlight to Professor**:
   - Show all 11 commits being processed from GitHub's REST API.
   - Show author attribution resolving Dhruv Gupta and Nistha Agarwal.
   - Show the dynamic decisions extracted from real commit messages and AST entities.
5. **Key Talking Point**:
   > *"Context Engine isn't just a static mockup. Here it is connecting to live GitHub data, extracting AST entities, and structuring engineering memory for real open-source software."*

---

## 3. Anticipated Faculty Questions & Model Answers

### Q1: *"How does Context Engine guarantee that decisions are not hallucinated?"*
> **Answer**: *"We enforce a mechanical invariant at the data model level (`backend/models.py`). Any decision with state `accepted` requires at least one non-empty evidence event linkage. Furthermore, our explanation engine strictly extracts sentences grounded in raw event passages and provides direct clickable source URLs."*

### Q2: *"Why did you use standard library HTTP server instead of Flask or FastAPI?"*
> **Answer**: *"To eliminate dependency bloat and guarantee zero-install reproducibility. Any machine with standard Python 3.11+ can immediately clone and run `python server.py` without virtual environments or `pip install` failures."*

### Q3: *"How does the system work on GitHub Pages without a backend?"*
> **Answer**: *"We built a dual-mode client interceptor (`clientMockApi` in `app.js`) that synchronizes with `static_data.js` and `localStorage`, while leveraging client-side GitHub REST API calls to parse public repositories directly in the browser."*
