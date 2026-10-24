# Context Intelligence Framework — System Explanation Guide

> **A Complete, Clear Walkthrough of How the System Works**  
> Written in simple, straightforward language so you can understand every line of code and confidently answer any questions from your professor.

---

## 1. The Core Idea: Why Did We Build This?

When programmers write code on GitHub:
- Git tracks **what** changed: *"Line 25 was replaced with `output = Kp * error`"*.
- But Git completely forgets **why** it was changed: *"Why did we choose Kp*error? Did someone test another formula first? Did the server crash last week?"*

When senior engineers leave a company, all that reasoning leaves with them. New engineers end up asking the same questions, trying ideas that already failed, or accidentally putting back old bugs.

### What our framework does:
Our software scans the repository's history (commits, GitHub issues, pull request arguments, and architect notes). It connects the dots and produces a **living decision history**. 

Whenever a developer clicks on any function in the project, our app tells them:
1. **What incident triggered this change** (e.g. *"Issue #12: Chamber overheated to 94°C"*).
2. **What alternatives were considered and rejected** (e.g. *"Marcus proposed idea A, but it increased delay by 17%"*).
3. **What was accepted and who decided it** (e.g. *"Sarah adopted discrete PID control with ADR 0004"*).
4. **Clickable proof** (direct links to the actual GitHub commit and comment).

---

## 2. The 3-Step Journey: How Data Moves Through the System

Here is the entire system pipeline in one clear diagram:

```text
  STEP 1: COLLECT DATA (Ingestion)
  Reads Git commits, GitHub issues, PR review discussions, and Markdown ADR notes.
  Every single event is given a real, clickable link back to GitHub.
                           │
                           ▼
  STEP 2: CONNECT & ANALYZE (The Brain)
  • Finds which files & functions were touched (using Python's AST parser).
  • Links discussions to decisions, and decisions to code.
  • Checks if two developers disagree (Conflict Detection).
  • Checks if new code breaks past agreements (Drift Detection).
                           │
                           ▼
  STEP 3: SHOW & TRIAGE (The Web Dashboard)
  • Displays the visual Timeline, Interactive Graph, and Code-Context view.
  • Provides a Review Queue where humans can approve or correct anything uncertain.
```

---

## 3. Tour of the Codebase (Which File Does What?)

Here is how our code is split up and what each file actually does:

### 📁 1. The Blueprint & Storage (`backend/models.py` & `backend/db.py`)
- [`backend/models.py`](backend/models.py):
  - Defines the core objects:
    - **`Event`**: An individual action from history (a commit, an issue, or a comment).
    - **`Decision`**: A choice made by a developer (has a state: `proposed`, `accepted`, `rejected`, `superseded`, or `unresolved`).
    - **`Entity`**: A specific piece of code (like a file or a Python function).
    - **`Edge`**: A connection between two items (e.g., *Decision A affects Function B*).
- [`backend/db.py`](backend/db.py):
  - Creates the SQLite database tables.
  - **The Golden Rule (Invariant):** The code physically blocks saving any decision that doesn't have evidence attached! If a decision has no proof, the system forces it to be labeled as `unresolved`. This enforces the grounding invariant that every decision has evidence.

---

### 📁 2. The Collectors (`backend/ingestion/`)
- [`backend/ingestion/git_adapter.py`](backend/ingestion/git_adapter.py):
  - Reads Git commit history, parses commit messages, extracts which files changed, and builds a clickable URL (`https://github.com/.../commit/...`).
- [`backend/ingestion/github_adapter.py`](backend/ingestion/github_adapter.py):
  - Reads GitHub Issues and Pull Requests.
  - Understands phrases like *"Closes #12"* to link a pull request back to the original bug report.
  - Ingests code review comments where developers debated the pros and cons.
- [`backend/ingestion/adr_adapter.py`](backend/ingestion/adr_adapter.py):
  - Reads Markdown files inside `docs/adr/`.
  - Parses standard decision records that follow the Nygard format: *Title*, *Status*, *Context*, *Decision*, and *Consequences*.
- [`backend/ingestion/identity.py`](backend/ingestion/identity.py):
  - Developers use different usernames in different places (e.g., `schen` on GitHub vs `sarah.chen@acme.org` in Git commits). This file maps them all to one canonical person: `Sarah Chen`.

---

### 📁 3. The Brain & Analysis (`backend/engine/`)
- [`backend/engine/entity_res.py`](backend/engine/entity_res.py):
  - Uses Python's built-in **AST (Abstract Syntax Tree)** library to scan python code and detect exact function names (like `def regulate_temperature`).
  - This allows the system to attach decisions to a specific function rather than just a whole 1,000-line file.
- [`backend/engine/graph.py`](backend/engine/graph.py):
  - Builds the **Temporal Context Graph**. It tracks relationships over time.
  - For example, if Decision B replaces Decision A, it marks Decision A as `superseded` and updates the timeline.
- [`backend/engine/reconciliation.py`](backend/engine/reconciliation.py):
  - **Conflict Detector:** If Developer 1 proposes an in-memory cache, and Developer 2 proposes a Redis cluster for the exact same file, this file catches the contradiction, creates a red conflict line, and alerts the Review Queue.
- [`backend/engine/drift_detector.py`](backend/engine/drift_detector.py):
  - **The CI Guard Dog:** Whenever new code is written in a pull request diff, this file checks if the new code violates a past accepted decision, or if someone accidentally re-introduced an idea that was already tested and rejected.
- [`backend/engine/explanation.py`](backend/engine/explanation.py):
  - When the user clicks on a function and asks *"Why does this exist?"*, this file builds the answer strictly using the verified evidence links from the graph according to the grounding invariant, abstaining when evidence is missing.

---

### 📁 4. The Server & Web App (`server.py` & `web/`)
- [`server.py`](server.py):
  - A lightweight, built-in Python web server. Runs on port 8080.
- [`backend/api.py`](backend/api.py):
  - The API layer that handles requests from the browser (e.g., getting timeline events, querying the graph, running drift checks, or clicking buttons in the review queue).
- [`web/index.html`](web/index.html) & [`web/style.css`](web/style.css) & [`web/app.js`](web/app.js):
  - The modern single-page dashboard.
  - Draws the SVG node-link graph, the horizontal timeline, the code-context accordion, the review queue triage modals, and the live drift testing tool.

---

### 📁 5. The Test & Evaluation Suite (`backend/evaluation/` & `run_demo.py`)
- [`backend/evaluation/ground_truth.py`](backend/evaluation/ground_truth.py):
  - A test dataset containing 32 real, manually verified decisions with their exact expected states and proof links.
- [`backend/evaluation/benchmark.py`](backend/evaluation/benchmark.py):
  - Calculates our project's accuracy scores (Precision, Recall, F1 score, Evidence link accuracy, and speed).
  - Compares our scores against 3 existing baselines (Normal Grep search, GitHub Copilot Q&A, and manual ADRs).
- [`run_demo.py`](run_demo.py):
  - A one-click test runner that automatically executes 21 checks across the entire system to verify everything is working properly.

---

## 4. The Two Synthetic Scenarios in Our Prototype

To make this prototype realistic, we built two simulated engineering scenarios into our database:

### Story 1: The Thermal Regulation System (`thermal-control-system`)
1. **The Bug:** During a long test run, the thermal chamber overheated to 94°C because the old system was just an ON/OFF switch (Issue #12).
2. **The Debate:** Marcus suggested tuning the ON/OFF threshold deadband. Sarah benchmarked it in simulation and proved it increased latency by 17% and still overheated.
3. **The Decision:** Sarah wrote ADR 0004 adopting a continuous mathematical PID controller with anti-windup clamping.
4. **The Code:** Sarah committed the PID code in `src/thermal/control.py`.
5. **The Drift Test:** Later, a junior engineer tried to submit a PR removing the PID math and putting back the simple ON/OFF switch. Our system immediately caught it and raised an alarm!

### Story 2: The Distributed Cache Service (`distributed-cache-service`)
1. **The Bug:** During a flash sale, servers ran out of memory (OOM crash) because keys were stored in a local Python dictionary (Issue #34).
2. **The Conflict:** Marcus submitted PR #38 trying to keep the local dictionary by adding a memory cap. Priya argued that local dictionaries cause stale data across server replicas and insisted on a Redis cluster.
3. **The Supersession:** Priya's Redis decision (ADR 0009) superseded Marcus's proposal.
4. **The Drift Test:** If someone tries to commit code with a local dictionary `local_cache = {}`, the drift detector flags it as defying the Redis decision.

---

## 5. Answers to Questions Your Professor Might Ask

**Q: Is this just a wrapper around ChatGPT or Copilot?**  
> *"No, Professor. Chatbots like ChatGPT or Copilot respond to questions probabilistically and often generate plausible-sounding explanations without provenance. Our system is an engineered temporal graph model. The core work is the event model, relational database invariants, AST function resolution, conflict detection, lifecycle state transitions, and CI drift checks. An LLM is only used as a helper for phrasing."*

**Q: Why do you need a graph instead of a normal database table?**  
> *"Because software history is a network of relationships over time. A decision links to multiple issues, touches specific functions, and can supersede earlier decisions. Our graph uses time-bounded edges (`valid_from` and `valid_to`) so we can query what the team believed was true at any specific date in history."*

**Q: How do you enforce grounding and prevent unsupported claims?**  
> *"We enforce a strict database invariant: every decision must have at least one verified evidence pointer with a clickable URL. If the system cannot find evidence, it is forced to return 'unresolved'. When explaining code, facts come strictly from graph citations. On unrecorded topics, the system abstains on 64.4% of cases; grounding invariants prevent unevidenced decisions from persisting in the graph."*

**Q: How does the decision extraction pipeline work?**  
> *"The extractor uses deterministic heuristic pattern matching (with conventional commit filtering) and an optional LLM-assisted extractor behind a standard interface. Any candidate decision must pass a strict Grounding Validator: all cited event IDs must exist in the bundle, and at least 50% of the rationale content words must appear in the cited source text. Otherwise, the decision is downgraded to 'unresolved' and routed to the Human Review Queue."*

**Q: How does GitHub Pages work compared to the full backend engine?**  
> *"GitHub Pages serves static web assets and reads a frozen, deterministic JSON snapshot (`static_data.js`) compiled directly from the Python API via `tools/build_static.py`. When run with `python server.py` or via Docker, the web application connects to the live Python REST API. A mode badge in the top navigation bar dynamically shows whether the dashboard is running on the 'Live engine' or 'Static snapshot'."*

**Q: What is the Human Review Queue for?**  
> *"In real engineering, automated tools cannot be 100% trusted blindly. When an extraction has low confidence, or when two developers submit conflicting proposals, or when code drifts from a decision, the system places it into the Review Queue. Human engineers can Confirm, Correct, Merge, or Reject the record."*
