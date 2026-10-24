# Presenter Notes & Demo Script (Speaker Notes)

> **Notice:** These are internal speaker notes and presentation coaching for demonstrating the Context Intelligence Framework to an audience or examination panel. These are speaker notes, not formal project documentation. For official project architecture, installation, and evaluation details, see [`readme.md`](../../readme.md).

---

## 1. Quick Presentation Outline (1-Minute Opening)
> *"Professor / Reviewers: Software teams lose institutional memory when developers leave. New developers can see what code was changed via Git, but Git does not record WHY decisions were made, what alternatives failed, or who approved them.*
> *The Context Intelligence Framework (CIF) bridges this gap: it ingests Git history, GitHub issues, pull request discussions, and architecture decision records into a temporal context graph with strict evidence grounding. It reconstructs architectural decision lifecycles, explains code context on demand, and blocks architectural regressions in CI before bad code merges."*

---

## 2. Complete Demo Walkthrough (Step-by-Step Script)

### Step 1: The Project Timeline & Historical "As-Of" Query
- **Navigation:** Click **Project Timeline** in the sidebar.
- **On Screen:** Chronological decision cards and the Historical "As Of" Query / Counterfactual Explorer.
- **Talking Points:**
  > *"Here is our Project Timeline showing the evolution of architectural choices over time. For example, on January 10th, Bug #12 occurred where machine overheating was observed. On January 12th, an idea to use a simple deadband threshold switch was rejected due to latency and overshoot. On January 15th, an architectural note was accepted to adopt a mathematical PID controller with anti-windup clamping.*
  > *Notice our Time-Travel capability! By executing an 'As Of' query set to January 1, 2026, the system reconstructs historical state before the PID decision was recorded. The PID controller disappears from the active set, proving our temporal graph eliminates retroactive information leakage."*

---

### Step 2: The Temporal Context Graph
- **Navigation:** Click **Context Graph** in the sidebar.
- **On Screen:** Interactive force-directed network showing decisions (green/red), code entities (blue), and GitHub events (pink).
- **Talking Points:**
  > *"This is the Temporal Context Graph. Green nodes represent accepted decisions, red nodes represent rejected alternatives, blue nodes represent code entities (files and functions extracted via Python AST), and pink nodes represent verified GitHub events.*
  > *Notice the red dashed connection: our reconciliation engine automatically flags active contributor disagreements when contradictory approaches are proposed for the same subsystem."*

---

### Step 3: Code-Context View (Function-Level Explanation)
- **Navigation:** Click **Code-Context View** in the sidebar. Select `src/thermal/control.py::regulate_temperature`.
- **On Screen:** Architectural decision chain and evidence summary for the selected function.
- **Talking Points:**
  > *"This is the core developer view. When a developer inspects a function, CIF synthesizes a grounded architectural explanation answer:*
  > *1. Why it exists: Sarah Chen implemented PID regulation to eliminate thermal runaway.*
  > *2. What failed: An on-off deadband switch was tested and rejected (17% higher latency).*
  > *3. Mechanical invariant: Every claim links directly to verified commit SHAs, PR discussions, and ADRs. Ungrounded claims are blocked at the database layer."*

---

### Step 4: Decision Explorer & Evidence Panel
- **Navigation:** Click **Decision Explorer** and **Evidence Panel**.
- **Talking Points:**
  > *"Developers can search across all recorded decisions, inspect alternatives considered, and examine the verified evidence audit trail with direct links to GitHub."*

---

### Step 5: Human Review Queue
- **Navigation:** Click **Review Queue** in the sidebar.
- **Talking Points:**
  > *"CIF follows a human-in-the-loop philosophy. High-risk actions, low-confidence decisions, and contributor conflicts are routed to this queue where maintainers confirm, correct, or reject proposals."*

---

### Step 6: Live CI Code-Drift Check & Guard Rules
- **Navigation:** Click **Live CI Drift Check**.
- **Action:** Select **Scenario 1: Thermal Revert (Reintroduces Rejected On-Off)** and click **Run CI Drift Detection Pass**.
- **On Screen:** Red alert flagging code drift and guard rule violation.
- **Talking Points:**
  > *"This demonstrates active regression prevention in CI. When a pull request diff reintroduces a previously rejected pattern (such as an on-off deadband), CIF's drift detector catches the violation in milliseconds, cites the historical rejection record, and blocks the regression before merge."*

---

### Step 7: Evaluation Metrics & Benchmark Honesty
- **Navigation:** Click **Metrics & Baselines** in the sidebar.
- **Talking Points:**
  > *"We evaluated CIF on WhyBench-Synth across 71 questions (26 positive, 45 unrecorded-topic negatives) from three domain repositories.*
  > *On Task 1 (Evidence Retrieval), BM25 keyword search achieves 92.3% retrieval on positive questions while CIF achieves 80.8% decision-evidence match. CIF's core contribution is Task 2: 100% state accuracy on matched decisions (21/21, small n) and 64.4% refusal accuracy (29/45) on unrecorded topics where standard LLMs hallucinate.*
  > *All metrics are computed dynamically from verifiable data manifests."*

---

## 3. Answering Anticipated Examination Questions

### Q1: *"Why not just use a Markdown README or an ADR directory?"*
> *"ADRs are static and disconnected from code evolution. On WhyBench-Synth, documentation-only retrieval found only 23.1% of relevant rationale because critical technical decisions live in pull request review comments, commit diffs, and issue debates. Furthermore, static markdown files cannot automatically evaluate PR diffs in CI to prevent architectural drift."*

### Q2: *"Why not just prompt ChatGPT or an LLM on the repository?"*
> *"General LLMs hallucinate plausible-sounding justifications and cite nonexistent commit hashes or PRs. CIF enforces a mechanical evidence invariant at the database layer: a decision cannot be persisted without links to real event records. Furthermore, CIF provides deterministic guard-rule synthesis without per-query inference costs or API key dependencies."*

### Q3: *"How does CIF resolve conflicting decisions from different engineers?"*
> *"The reconciliation engine matches decisions affecting overlapping entities and checks for contradictory lifecycle states and semantic conflict pairs using whole-word boundary matching. Conflicts are surfaced in the Temporal Context Graph and routed to the Human Review Queue rather than silently merged."*
