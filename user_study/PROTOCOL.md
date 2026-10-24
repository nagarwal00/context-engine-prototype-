# User Study Protocol: Context Intelligence Framework Evaluation

## 1. Study Objective
The objective of this controlled user study is to evaluate whether the **Context Intelligence Framework (CIF)** enables software engineers to investigate architectural decisions faster, more accurately, and with higher confidence compared to standard codebase search (e.g., GitHub file and commit search / local grep).

---

## 2. Study Design
- **Methodology:** Within-subjects controlled trial with counterbalanced condition assignment.
- **Participants:** Target sample size: $5 \le N \le 8$ software engineering students or professional developers with Git familiarity.
- **Tasks:** Two architectural rationale investigation tasks (Task A and Task B) drawn from the development dataset on realistic software components.
- **Counterbalancing:** Participants are alternated across two conditions to mitigate order and learning bias:
  - *Group 1 (Odd IDs: P01, P03, P05, P07):* Task A using CIF $\rightarrow$ Task B using Baseline Search.
  - *Group 2 (Even IDs: P02, P04, P06, P08):* Task A using Baseline Search $\rightarrow$ Task B using CIF.

---

## 3. Conditions & Tools
1. **Condition 1: CIF (Context Intelligence Framework):**
   - Access to the CIF Web Dashboard (`/` running on localhost:8080) and repository decision graph.
   - Participants can query decisions, view temporal decision lifecycles, and inspect grounded evidence links.
2. **Condition 2: Baseline Code Search:**
   - Access to the target repository source code, commit history (`git log`), pull request discussions, and documentation.
   - Standard tools allowed: GitHub UI search, `git log`, `grep`/IDE keyword search.

---

## 4. Dependent Variables & Metrics
For each trial, the investigator records:
1. **Time-to-Answer (`time_seconds`):** Elapsed time from task start until the participant submits their answer. Capped at 10 minutes (600 seconds).
2. **Answer Correctness (`correct`):** Binary score ($1 = \text{correct}$, $0 = \text{incorrect}$) scored against pre-established ground-truth criteria.
3. **Subjective Confidence (`confidence`):** 1–5 Likert scale ($1 = \text{Very Low Confidence}$, $5 = \text{Very High Confidence}$) reported immediately post-task.
4. **Qualitative Observations (`notes`):** Participant comments, navigation bottlenecks, and search strategies.

---

## 5. Trial Procedure (Total Time: ~25 minutes per participant)
1. **Briefing & Consent (3 minutes):**
   - Participant reads and signs [`CONSENT.md`](file:///user_study/CONSENT.md).
   - Investigator explains the study rules: 10-minute cap per task, think-aloud optional.
2. **Tool Orientation (2 minutes):**
   - Brief 1-minute walkthrough of the CIF UI interface (search bar, decision detail view, evidence drawer).
3. **Task 1 Execution (Up to 10 minutes):**
   - Participant receives Task 1 prompt according to counterbalancing schedule.
   - Investigator starts stopwatch; participant stops when they state their answer.
   - Participant rates confidence (1–5).
4. **Task 2 Execution (Up to 10 minutes):**
   - Participant receives Task 2 prompt with the alternative tool.
   - Stopwatch runs; participant submits answer and rates confidence (1–5).
5. **Debriefing & Feedback (2 minutes):**
   - Brief qualitative questions: "Which tool felt more natural? What evidence did you trust most?"

---

## 6. Ethical Considerations & Data Management
- Participation is 100% voluntary and anonymous.
- Raw observation logs are stored in `user_study/results_template.csv` using participant codes (`P01`–`P08`).
- No participant names, emails, or personal identifiers are stored or published.
