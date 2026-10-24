# Context Intelligence Framework — Simple Project & Demo Guide

> **Welcome!** This guide explains our project in **easy, everyday language**.  
> If you have to present this project to your professor, this document will teach you exactly what the project does, what every button on the screen does, and what words to say during your presentation.

---

## 1. What is this project about? (The 1-Minute Summary)

When developers write code on GitHub, they save their code using **commits** and **pull requests**.
- Git tells you **WHAT** code was changed.
- But Git **does NOT tell you WHY** the developer wrote it that way.

### The Real-World Problem:
Imagine an engineer named Sarah writes a complex temperature control formula. A few months later, Sarah leaves the company. A new junior developer joins the team, looks at Sarah's code, and thinks:  
*"Why is this math so complicated? I'll just replace it with a simple ON/OFF switch."*  

The junior developer doesn't realize that 6 months ago, that simple ON/OFF switch caused a real machine to overheat and catch fire! The explanation was buried in an old chat or closed bug report that nobody can find.

### What our software does:
Our software acts like a **smart project detective**. It reads:
1. All old code commits
2. All reported bug tickets (GitHub Issues)
3. All debates between developers (Pull Request review comments)
4. All architecture notes (written by lead developers)

It links them all together into a visual storyline. Now, whenever any developer clicks on any piece of code, our system explains:
- **What problem originally happened**
- **What ideas were tried, tested, and rejected (and why they failed)**
- **What final solution was agreed upon and who decided it**
- **Direct clickable links to the real GitHub discussions as proof**

---

## 2. Plain English Dictionary (What Every Term Means & Where It Lives in Code)

If your professor asks you technical questions, here are the simple explanations and the exact Python files responsible:

### 1. "Provenance" / Evidence Grounding
- **In simple words:** Having **proof for every claim**. The system is strictly forbidden from guessing or making up stories (unlike ChatGPT). Every explanation must give you a clickable link to the exact commit or discussion comment where that decision was made.
- **Handled by:** [`backend/models.py`](file:///c:/Users/HP/Desktop/SE_project/backend/models.py) and [`backend/db.py`](file:///c:/Users/HP/Desktop/SE_project/backend/db.py). The database will physically crash with an error if someone tries to save a decision without proof!

### 2. "ADR" (Architectural Decision Record)
- **In simple words:** A short document where lead engineers write down major choices. For example: *"We decided to switch from local computer memory to Redis servers because our servers kept running out of RAM."*
- **Handled by:** [`backend/ingestion/adr_adapter.py`](file:///c:/Users/HP/Desktop/SE_project/backend/ingestion/adr_adapter.py). It reads markdown files in the project documentation.

### 3. "AST" (Abstract Syntax Tree)
- **In simple words:** Python's built-in tool for inspecting code. Instead of just looking at an entire 500-line file, AST allows our software to identify the exact name of each function (like `def regulate_temperature`), so our system can track individual functions over time.
- **Handled by:** [`backend/engine/entity_res.py`](file:///c:/Users/HP/Desktop/SE_project/backend/engine/entity_res.py).

### 4. "Temporal Context Graph"
- **In simple words:** A visual web of colored circles (nodes) and lines (connections) showing how bug tickets, decisions, and code files relate to each other **over time**.
- **Handled by:** [`backend/engine/graph.py`](file:///c:/Users/HP/Desktop/SE_project/backend/engine/graph.py).

### 5. "Reconciliation" / Conflict Detection
- **In simple words:** Detecting when two developers disagree. For example, Marcus submits code using local computer memory, while Priya submits a document saying we must use Redis. The system flags this contradiction in red so humans can resolve the disagreement.
- **Handled by:** [`backend/engine/reconciliation.py`](file:///c:/Users/HP/Desktop/SE_project/backend/engine/reconciliation.py).

### 6. "Code Drift Detection"
- **In simple words:** Catching a developer who accidentally breaks an agreed decision. For example, if someone opens a pull request that puts back the old rejected ON/OFF switch, our system catches it in real time and raises an alarm.
- **Handled by:** [`backend/engine/drift_detector.py`](file:///c:/Users/HP/Desktop/SE_project/backend/engine/drift_detector.py).

### 7. "Review Queue"
- **In simple words:** An inbox for human engineers. If our system detects a conflict between two developers, or if a code change looks suspicious, it puts that item into this inbox so a human can click **Confirm**, **Correct**, or **Reject**.
- **Handled by:** [`backend/api.py`](file:///c:/Users/HP/Desktop/SE_project/backend/api.py) and the web interface.

### 8. "GitHub App & CI Integration"
- **In simple words:** Integrates with GitHub to inspect pull request diffs in CI and automatically flag architectural regressions.
- **Testing status:** *webhook/CI verified with mocks only* (automated test suite in `tests/test_webhook.py` using HMAC-SHA256 signature fixtures; live production deployment requires public IP/tunnel per `GITHUB_APP_SETUP.md`).
- **Handled by:** [`backend/api.py`](file:///c:/Users/HP/Desktop/SE_project/backend/api.py) (`/api/webhook/github`), [`tools/ci_check.py`](file:///c:/Users/HP/Desktop/SE_project/tools/ci_check.py), and [`.github/workflows/cif-check.yml`](file:///c:/Users/HP/Desktop/SE_project/.github/workflows/cif-check.yml).

---

## 3. How to Run the Project (Step-by-Step)

You do **NOT** need to install any external packages, tools, or Node.js. It runs on standard Python 3.

### Step 1: Initialize Database & Seed Pilot Repositories
On a fresh checkout, run the database initializer to apply all migrations and populate the pilot repositories:
```bash
python tools/init_db.py --seed
```

### Step 2: Start the Server
Open your terminal (PowerShell or Command Prompt) in this project folder and type:
```bash
python server.py
```

You will see:
```text
======================================================================
  Context Intelligence Framework -- Living Decision History Prototype
======================================================================
[OK] Existing database loaded with decisions.

[SERVER LIVE] Prototype is live and running at: http://127.0.0.1:8080/
[*] Serving interactive Context Graph, Review Queue, and all UI surfaces.
```

### Step 3: Open Your Browser
Open any web browser (Google Chrome, Edge, Safari, Firefox) and go to:  
👉 **http://127.0.0.1:8080/**

You will see the full interactive dark-mode dashboard!

---

### Step 3: Deploy to GitHub Pages (Live Web Demo)

This repository is pre-configured to deploy directly on GitHub Pages with **zero extra services or paid hosting**:
- **Automatic GitHub Pages workflow:** `.github/workflows/deploy.yml` deploys the web interface automatically on every push.
- **Classic Branch deployment:** The `docs/` folder contains the static distribution for 1-click branch deployment.
- **Client-Side Data Engine:** All interactive UI surfaces, graph, CI drift checking, and review actions work 100% in the browser on GitHub Pages (run `python tools/print_facts.py` to inspect live counts of surfaces, migrations, tests, and benchmark questions).

See [DEPLOYMENT.md](file:///c:/Users/HP/Desktop/SE_project/DEPLOYMENT.md) for full step-by-step instructions.

---

## 4. What is `run_demo.py` and How Does It Work?

### What it is:
`run_demo.py` is an **automated test script** that tests all 21 core features of the system in 3 seconds. It is the best tool to prove to your professor that the code is real, working, and not faked.

To run it, open a terminal and type:
```bash
python run_demo.py
```

### What it tests (in simple words):
1. **Rule Test:** It tries to sneak a decision into the database with zero evidence. The database blocks it, proving our grounding invariant works.
2. **Collector Tests:** It tests that Git commits, GitHub issues, and PR comments are correctly read and given clickable URLs.
3. **Code Reader Test (AST):** It feeds a snippet of Python code and tests that the system finds the function names automatically.
4. **Detective Query Test:** It asks the system *"Why does `regulate_temperature` exist?"* and tests that it correctly lists the history in order.
5. **Conflict Test:** It checks that when Marcus and Priya disagree, the system spots the conflict.
6. **Drift Test:** It feeds a bad code change into the system and checks that the system catches the violation.
7. **Abstention Test:** It asks about a fake file that does not exist. It verifies that the system abstains with *"No decision found"* when no evidence exists.
8. **Scorecard:** It calculates computed accuracy and grounding metrics from real data (see [`evaluation_results.md`](file:///c:/Users/HP/Desktop/SE_project/evaluation_results.md)).

> **Verified Counts from Live Code & Data**:
> To inspect machine-verified counts of automated test cases, migrations, benchmark questions, and UI surfaces directly from data, run:
> ```bash
> python tools/print_facts.py
> ```

---

## 5. Complete Demo Walkthrough (What to Click & What to Say to Your Professor)

When demoing this project to your professor, follow these 8 simple steps:

---

### 🎙️ Introduction (Say this first):
> *"Professor, software teams lose institutional memory when developers leave. New developers can see what the code does, but not why it was written that way. Our project connects Git history, GitHub discussions, and architecture notes into a living timeline so teams never repeat past mistakes."*

---

### 🖥️ Step 1: The Project Timeline & Historical Time-Travel ("As-Of" Query)
- **Action:** Click **Project Timeline** in the left sidebar.
- **What is on screen:** A chronological list of decision cards plus the Historical "As Of" Query & Counterfactual Explorer.
- **What to say:**
  > *"Here is our Project Timeline. It shows the evolution of the project over time. For example, on January 10th, Bug #12 occurred where the machine overheated. On January 12th, an idea to use a simple deadband switch was rejected. On January 15th, an architectural note was accepted to use a mathematical PID controller. We can filter the timeline by Accepted, Rejected, or Superseded decisions."*
- **Action:** In the "Historical 'As Of' Query & Counterfactual Explorer", click the preset button **"Before PID Adoption (2026-01-01)"** and click **"Execute Historical Query"**.
- **What to say:**
  > *"Notice our Time-Travel capability! By setting the historical cutoff date to January 1, 2026, the system reconstructs exactly what the team knew before the PID decision was made. The PID controller decision disappears from the active state, proving that our temporal graph eliminates retroactive information leakage."*
- **Action:** Click **"After PID Acceptance (2026-03-01)"** and run it to watch the PID decision return as the active architectural standard.

---

### 🖥️ Step 2: The Context Graph
- **Action:** Click **Context Graph** in the left sidebar.
- **What is on screen:** An interactive visual map of circles and connecting lines.
- **What to say:**
  > *"This is the Temporal Context Graph. It visually maps out the entire project. Green circles are accepted decisions, red circles are rejected ideas, blue circles are code files, and pink circles are real events from GitHub.*  
  > *Notice this red dashed line: our system detected an active disagreement between two engineers who proposed contradictory solutions for the same file."*
- **Action:** Click on any circle on the graph to open its details inspector on the right.

---

### 🖥️ Step 3: The Code-Context View (The Core Feature!)
- **Action:** Click **Code-Context View** in the left sidebar.
- **Action:** On the left list, click on `src/thermal/control.py::regulate_temperature`.
- **What is on screen:** An explanation banner and a step-by-step decision history.
- **What to say:**
  > *"This is the heart of our software. A developer simply selects a function, and the system answers: 'Why does this code look like this?'.*  
  > *Look at the decision chain below:*  
  > *- Step 1 (Rejected): An engineer tried a simple ON/OFF deadband switch, but simulation showed it caused 17% higher latency and still overheated.*  
  > *- Step 2 (Accepted): Lead architect Sarah Chen implemented a continuous PID math formula with anti-windup clamping to keep the temperature stable.*  
  > *Notice that every step has clickable links back to the original GitHub issue and commit. The system provides proof for everything."*

---

### 🖥️ Step 4: Decision Explorer & Evidence Panel
- **Action:** Click **Decision Explorer**. Show the search box (type `"PID"` or `"Redis"`).
- **What to say:**
  > *"Developers can search through all recorded decisions, see alternatives that were considered, and inspect why certain ideas were turned down."*
- **Action:** Click **Evidence Panel**. Select any decision from the dropdown.
- **What to say:**
  > *"The Evidence Panel is our audit trail. It displays the raw GitHub comment, the commit diff, and verified links that open the source on GitHub."*

---

### 🖥️ Step 5: Human Review Queue
- **Action:** Click **Review Queue** in the left sidebar.
- **What to say:**
  > *"No AI system should make final architectural decisions on its own. Whenever our system detects a contradiction between developers, or whenever confidence is low, it routes the item to this Review Queue.*  
  > *A human engineer can click Confirm, Correct, or Reject to keep the project record accurate."*
- **Action:** Click **Confirm** on one item to show that the queue updates live!

---

### 🖥️ Step 6: Live CI Code-Drift Check & Decision Guard Rules (The Headline Novelty!)
- **Action:** Click **Live CI Drift Check** in the left sidebar.
- **Action:** Click the button that says **Scenario 1: Thermal Revert (Reintroduces Rejected On-Off)**.
- **Action:** Click **Run CI Drift Detection Pass**.
- **What happens on screen:** A red warning banner immediately pops up flagging both historical drift and active Guard Rule violations!
- **What to say:**
  > *"This simulates a developer opening a new Pull Request. In this scenario, a developer tried to delete the PID math and put back the old ON/OFF switch.*  
  > *Our system analyzed the diff against historical decisions and active Guard Rules, caught the violation in real time, warned the team that it reintroduces a previously rejected approach, and linked directly to the evidence trail in the Review Queue!"*
- **Action:** Click **Scenario 4: Consistent Code (Normal Refactor)** and run it to show that normal code changes pass cleanly.

---

### 🖥️ Step 7: Evaluation Metrics & Comparison Table
- **Action:** Click **Metrics & Baselines** in the left sidebar.
- **What is on screen:** Metric cards, WhyBench-Synth (hand-authored synthetic benchmark) results, and a baseline comparison table.
- **What to say:**
  > *"To validate our capstone honestly, we evaluated the system on WhyBench-Synth across 71 questions on the frozen `test_v2` split from three hand-authored synthetic domain repositories (acme-ecommerce/payment-core, cloud-hypervisor/cloud-hypervisor, cli/cli) and compared it to practical baselines.*  
  > *On Task 1 (Evidence Retrieval), on identical positive questions, Baseline A (BM25) achieves 92.3% and Baseline B (Docs-only) achieves 23.1% compared to CIF's 80.8% decision-evidence match (Footnote: CIF's metric is decision-evidence match, not ranked retrieval; BM25 retrieval is higher. CIF's value is state classification, abstention and guard rules). On Task 2 (Decision Reconstruction), CIF achieved 80.8% Strict Recall, 100.0% (21/21 matched decisions, small n) State Accuracy, and abstains correctly on 29/45 (64.4%) of unrecorded-topic questions (16/45 receive an unsupported decision — see LIMITATIONS). All metrics are computed dynamically from real manifests (see `evaluation_results.md`)."*

#### 💡 Answering the Professor: *"Why not just write a README or use an AI Agent?"*
If the professor challenges the project, say this:
> 1. *"Docs-only search achieved only 8.5% hit rate on WhyBench-Synth because architectural decisions live primarily in PR review debates, issues, and commit histories, not static docs—and a README cannot automatically block violating pull requests in CI."*  
> 2. *"General-purpose AI agents may generate answers without provenance and fail to abstain, whereas CIF achieved 100.0% (21/21 matched decisions, small n) state accuracy, abstains correctly on 29/45 (64.4%) of unrecorded-topic questions (16/45 receive an unsupported decision — see LIMITATIONS), and enforces a grounding invariant linking explanations directly to verified source events."*  
> 3. *"CIF converts accepted decisions into active CI Guard Rules that evaluate pull request diffs in milliseconds to prevent architectural regressions automatically."*

---

### 🖥️ Step 8: Onboarding Tour
- **Action:** Click **Onboarding Tour** in the left sidebar.
- **What to say:**
  > *"Finally, we created an Onboarding Mode. Instead of spending weeks reading through messy old pull requests, a new developer can read this 3-minute guided summary and understand the key reasons behind all core subsystems."*

---

## 6. How the Code is Structured (Simple Overview)

- [`server.py`](file:///c:/Users/HP/Desktop/SE_project/server.py): The main script that runs the web server.
- [`run_demo.py`](file:///c:/Users/HP/Desktop/SE_project/run_demo.py): The test script that runs the 21 automated checks.
- [`backend/db.py`](file:///c:/Users/HP/Desktop/SE_project/backend/db.py): The SQLite database storing decisions, events, and evidence.
- [`backend/engine/`](file:///c:/Users/HP/Desktop/SE_project/backend/engine/): The analysis brain (reads Python functions, finds conflicts, catches drift).
- [`backend/ingestion/`](file:///c:/Users/HP/Desktop/SE_project/backend/ingestion/): The collectors that read Git commits, GitHub issues, and ADR notes.
- [`backend/evaluation/`](file:///c:/Users/HP/Desktop/SE_project/backend/evaluation/): The benchmark engine that calculates accuracy scores.
- [`web/`](file:///c:/Users/HP/Desktop/SE_project/web/): The HTML, CSS, and JavaScript files for the browser interface.
- [`explanation.md`](file:///c:/Users/HP/Desktop/SE_project/explanation.md): In-depth, easy-to-read explanation of the codebase architecture.
- [`task.md`](file:///c:/Users/HP/Desktop/SE_project/task.md): Milestone progress tracking checklist (all 100% completed).
