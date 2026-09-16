# Context Intelligence Framework — Implementation Guide for Antigravity

> **Read this whole document before writing any code.** It explains not just *what* to build, but *why* each piece exists, so that implementation decisions you make in the gaps stay consistent with the project's intent. This is a 17-week university software-engineering capstone project, approved by the course instructor with a specific, narrowed scope (see §1). Every requirement below traces back either to the original feasibility report or to the instructor's approval feedback — nothing here is invented scope creep, and nothing in the approved scope has been dropped.

---

## 0. What you are building, in one paragraph

You are building a system that reconstructs **why** a software project looks the way it does — not just what changed, but the reasoning chain: *decision → alternatives considered → supporting discussion/experiment → code change → present implementation.* It ingests Git history, GitHub issues, pull requests, review discussions, ADRs, and documentation; extracts candidate decisions with an LLM; links every decision to the exact code artifact it affected; tracks each decision through a lifecycle (proposed → accepted/rejected/superseded/unresolved); detects when reasoning conflicts across contributors or when live code drifts from an accepted decision; and surfaces everything through a hosted web app with a human review queue for anything the system isn't confident about. It is **not** a chatbot over your repo and **not** a commit/PR summarizer — those are table stakes that existing tools already do (see §2).

---

## 1. Scope contract (do not violate this)

This section is the single most important constraint on the whole project. Read it twice.

**In scope — the required system:**
1. **Multi-source ingestion** — Git history, GitHub issues, PRs, review discussions, ADRs, and project docs, normalized into one common event format. Coding-assistant session ingestion is optional/additive, never a dependency of the core pipeline.
2. **Decision lifecycle** — every decision has a state (`proposed | accepted | rejected | superseded | unresolved`), an owner, a timestamp, the artifact(s) it touches, and the original evidence.
3. **Code ↔ decision linking** — a decision links to the exact repository, module, file, function, dependency, or config it affected. A user can select a code artifact and see why it looks the way it does.
4. **Reconciliation & drift detection** — detect conflicting reasoning between contributors/tools, detect when a later decision supersedes an earlier one, and detect when current code is inconsistent with (or reverts) an accepted decision.
5. **Evidence-grounded output** — every explanation cites the commit/issue/PR/discussion/ADR/doc that supports it. Insufficient evidence → the system says `unresolved`, never a confident guess.
6. **Human review queue** — low-confidence decisions, contradictions, and drift candidates go into a queue where a person can confirm, reject, merge, or correct the record.
7. **Hosted product** — a real hosted web app, wired to GitHub via a GitHub App/webhooks or CI integration, with six UI surfaces: project timeline, context graph, code-context view, decision explorer, evidence panel, and review queue.

**Explicitly out of scope / guardrails:**
- **Not** a general repository chatbot (no "ask anything about this repo" Q&A box as the main interface — that's Copilot's job, and it's already been done).
- **Not** a dashboard that merely summarizes commits and PRs (that's what GitHub's own UI, and a dozen analytics tools, already do).
- **Not** "only an LLM call over repository text." The LLM assists candidate extraction and phrasing of explanations. The substantial engineering — and the graded content of this project — is the event model, the temporal graph, entity resolution, provenance tracking, conflict detection, decision-state transitions, drift checks, and the evaluation pipeline.
- **Not** a CRUD app (you are not building forms over a database — most of the information already exists in messy history; the job is finding, connecting, and dating it).
- **Not** an n8n-style "when X happens, do Y" automation. The system continuously maintains a *model*, not a sequence of triggered actions.

Anchor every architectural decision back to this list. If a feature doesn't serve one of the seven required capabilities, cut it — this project has 17 weeks, not more.

---

## 2. Competitive positioning — know what you are and are not replacing

You will be evaluated against, and should explicitly benchmark against, the following systems. For each, be able to state in one sentence what it already does and what your system adds on top:

| System | What it already provides | What Context Intelligence Framework adds |
|---|---|---|
| **Continuum** | Context-window / memory continuity tooling for AI coding agents | Decision *lifecycle* modeling (accepted/rejected/superseded) with cross-source provenance, not just recall of prior context |
| **Context Graph** | Graph-based linking of code/project artifacts | Time-aware decision-state transitions + drift detection against live code, not a static link graph |
| **Warrant** | Evidence/justification tracking for claims | Software-engineering-specific entity resolution (file/function/module/dependency) and code-level drift checks |
| **GitHub Copilot (PR exploration)** | On-demand Q&A over PR/commit history | Always-on reconstruction of the full decision chain, contradiction detection across contributors, and a review queue — not query-response |
| **Glean for Engineering** | Cross-tool search (GitHub, Jira, Slack, docs) | Structured decision objects with lifecycle state, not search results |
| **Backstage** | Developer portal / software catalog | Automatically extracted history, not manually maintained catalog entries |
| **ADR Tools** | Structured manual ADR authoring | Automatic extraction of decisions from unstructured history, plus drift detection against ADRs already written |
| **Codebase Context** | Stores decisions/conventions, some Git-derived context | Multi-source (issues+PRs+reviews+docs, not just Git), lifecycle states, reconciliation, and drift detection |

Your defensible contribution, to say explicitly in the planning presentation and in code comments/README: **the evaluated combination** of multi-source decision reconstruction + code-level provenance + contributor reconciliation + decision-drift detection. No single competitor does all four; that combination, evaluated end-to-end, is the thesis of this project.

---

## 3. High-level architecture

```
                         ┌─────────────────────────────────────────┐
                         │              Data Sources                │
                         │  Git history · GitHub Issues · PRs ·      │
                         │  Review comments · ADRs · Docs (md/pdf)   │
                         │  (optional: coding-assistant exports)     │
                         └───────────────────┬───────────────────────┘
                                             │  connectors (per-source adapters)
                                             ▼
                         ┌─────────────────────────────────────────┐
                         │        Ingestion & Normalization          │
                         │  → common Event schema (§5)               │
                         │  → stable source links preserved          │
                         └───────────────────┬───────────────────────┘
                                             ▼
                         ┌─────────────────────────────────────────┐
                         │           Entity Resolution               │
                         │  same file/function/module/dependency/    │
                         │  decision referenced across sources →     │
                         │  resolved to one canonical entity node    │
                         └───────────────────┬───────────────────────┘
                                             ▼
                         ┌─────────────────────────────────────────┐
                         │      Decision Extraction (LLM-assisted)   │
                         │  candidate decisions, alternatives,       │
                         │  constraints, rationale                   │
                         └───────────────────┬───────────────────────┘
                                             ▼
                         ┌─────────────────────────────────────────┐
                         │       Temporal Context Graph (§7)         │
                         │  nodes: decisions, code artifacts,        │
                         │         events, people, evidence          │
                         │  edges: caused-by, supersedes, affects,   │
                         │         discussed-in, evidenced-by        │
                         └───────┬───────────────────────┬───────────┘
                                 ▼                        ▼
              ┌───────────────────────────┐  ┌───────────────────────────┐
              │  Evidence Validation &     │  │  Reconciliation & Drift    │
              │  Confidence Scoring        │  │  Detection (§8)            │
              └─────────────┬──────────────┘  └─────────────┬─────────────┘
                             ▼                               ▼
                         ┌─────────────────────────────────────────┐
                         │           Human Review Queue              │
                         │  confirm / reject / merge / correct       │
                         └───────────────────┬───────────────────────┘
                                             ▼
                         ┌─────────────────────────────────────────┐
                         │             Hosted Web App                │
                         │  Timeline · Context Graph · Code-Context  │
                         │  View · Decision Explorer · Evidence Panel│
                         │  · Review Queue                           │
                         └─────────────────────────────────────────┘
```

**Why this shape:** every arrow in this diagram corresponds to a required capability in §1. If you find yourself building a component that doesn't sit on this diagram, stop and ask whether it belongs in this project.

---

## 4. Recommended technology stack

Pick a stack the team already knows over a "better" unfamiliar one — 17 weeks is not enough time to learn a new stack *and* build this. The defaults below are chosen for a small student team and for how well each choice serves the graph + temporal + provenance requirements.

- **Language / backend:** Python 3.11+, FastAPI. Python has the best library support for Git parsing (`GitPython`, `pydriller`), GitHub API access (`PyGithub`), and LLM tooling.
- **Primary datastore:** PostgreSQL. Use it for the event log, decision records, and evidence links (relational integrity matters for provenance — you must never lose a source pointer).
- **Graph layer:** Do **not** stand up a separate graph database (Neo4j) unless the team has prior graph-DB experience — it adds an operational dependency for marginal benefit at this scale. Instead, model the temporal context graph as a node table + edge table in Postgres (`entities`, `edges`, both with `valid_from`/`valid_to` for time-awareness), and use recursive CTEs or a Python graph library (`networkx`) in-memory for traversal/queries. If the team has bandwidth after Milestone 2, Neo4j Community Edition is the natural upgrade path — design the edge schema so that migration is a data export/import, not a rewrite.
- **Vector search (for entity resolution / evidence retrieval):** `pgvector` extension on the same Postgres instance — avoids running a second database for embeddings.
- **Task queue:** Redis + Celery (or `arq` if the team prefers async-native) for ingestion jobs, LLM extraction jobs, and webhook processing — ingestion must not block the request/response cycle.
- **LLM access:** Anthropic Claude API (Claude models support long context, which matters for feeding multi-document evidence bundles, and strong instruction-following for the structured-output extraction prompts in §6.4). Use tool-use / structured JSON output mode for every extraction call — never free-text parsing.
- **Frontend:** React + TypeScript, Next.js. Use a graph-visualization library (`react-flow` or `d3` directly) for the Context Graph view, and a timeline library (or a custom `d3` timeline) for the Project Timeline.
- **GitHub integration:** GitHub App (not a personal access token) — required for the webhook-driven "hosted product" requirement in §1, and for scoping permissions correctly if this is ever installed on more than the team's own repos.
- **CI integration:** GitHub Actions, triggered on push/PR merge, to run the drift-check pass (see §8.3) against newly merged code.
- **Deployment:** containerize with Docker Compose for local dev; deploy to a single VM (or student cloud credits) for the hosted prototype — do not over-engineer deployment (no Kubernetes) for a 17-week prototype with one or two repos.

---

## 5. Event schema — the common data model

Every ingested item, regardless of source, is normalized into one `Event`. This is the single most important schema in the project: get it right in Milestone 1 and everything downstream (graph, extraction, drift detection) becomes tractable; get it wrong and you will be reworking ingestion in Milestone 3.

### 5.1 `Event`

```json
{
  "event_id": "uuid",
  "source_type": "git_commit | github_issue | github_pr | pr_review_comment | adr | doc | coding_assistant_session",
  "source_id": "string — the source system's native ID (commit SHA, issue number, etc.)",
  "source_url": "string — stable deep link back to the original item (required, never null)",
  "repo": "string — owner/repo",
  "author": "string — normalized author identity (see §6.5 identity resolution)",
  "timestamp": "ISO-8601",
  "title": "string | null",
  "body": "string — raw text content",
  "artifacts_touched": ["list of raw file paths, if applicable"],
  "parent_event_ids": ["list of event_ids this event references or replies to"],
  "raw_metadata": { "...source-specific fields, preserved as-is" }
}
```

**Why `source_url` is mandatory, not optional:** requirement §1.5 (evidence-grounded output) means every explanation the system ever produces must be traceable to a concrete, clickable source. If an ingestion adapter cannot produce a stable URL for an item, that adapter is not done.

### 5.2 `Decision`

```json
{
  "decision_id": "uuid",
  "title": "short human-readable summary",
  "state": "proposed | accepted | rejected | superseded | unresolved",
  "state_history": [
    { "state": "proposed", "changed_at": "ISO-8601", "changed_by": "event_id or user_id" }
  ],
  "made_by": "normalized identity",
  "made_at": "ISO-8601",
  "artifacts_affected": ["entity_id list — resolved code entities, not raw paths"],
  "alternatives_considered": [
    { "description": "string", "rejection_reason": "string | null", "evidence_event_ids": ["..."] }
  ],
  "rationale": "string — extracted, evidence-grounded explanation",
  "evidence_event_ids": ["list of Event.event_id supporting this decision — never empty unless state=unresolved"],
  "supersedes_decision_id": "uuid | null",
  "superseded_by_decision_id": "uuid | null",
  "confidence": "float 0.0–1.0 — extraction confidence, drives review-queue routing",
  "review_status": "auto_confirmed | pending_review | human_confirmed | human_rejected | human_merged | human_corrected"
}
```

**Why `evidence_event_ids` can never be empty for a non-`unresolved` decision:** this is the mechanical enforcement of the evidence-grounded requirement. Write a database constraint or application-level check for this — it should be structurally impossible to persist a confident decision with no evidence.

### 5.3 `Entity` (resolved code artifact)

```json
{
  "entity_id": "uuid",
  "entity_type": "repository | module | file | function | dependency | config",
  "canonical_path": "string — e.g. 'src/thermal/control.py::regulate_temperature'",
  "aliases": ["list of raw strings across sources that resolve to this entity"],
  "current_state_summary": "string — optional cached description of what it currently does"
}
```

### 5.4 `Edge` (temporal context graph)

```json
{
  "edge_id": "uuid",
  "edge_type": "caused_by | supersedes | affects | discussed_in | evidenced_by | conflicts_with | drifts_from",
  "from_id": "uuid — decision_id, entity_id, or event_id",
  "from_type": "decision | entity | event",
  "to_id": "uuid",
  "to_type": "decision | entity | event",
  "valid_from": "ISO-8601",
  "valid_to": "ISO-8601 | null — null means currently valid"
}
```

Time-bounding edges with `valid_from`/`valid_to` is what makes the graph *temporal* rather than a static snapshot — it's how you answer "what did we believe was true at time T" and detect supersession and drift.

---

## 6. Ingestion pipeline

Build one adapter per source. Every adapter's only job is: read from the source, emit `Event` objects, guarantee `source_url` is populated, and be idempotent (re-running ingestion must not create duplicate events — upsert on `(source_type, source_id, repo)`).

### 6.1 Git history adapter
- Use `pydriller` to walk commit history. Emit one `Event` per commit (`source_type: git_commit`), with `artifacts_touched` = changed file paths, `body` = commit message, `source_url` = `https://github.com/{repo}/commit/{sha}`.
- Also emit a diff summary (function-level, using `pydriller`'s modified-methods detection) into `raw_metadata` — this is what entity resolution will use to detect function-level changes, not just file-level.

### 6.2 GitHub Issues & PRs adapter
- Use `PyGithub` (or GitHub's GraphQL API directly for efficiency on large repos) to pull issues, PRs, and PR review comments.
- Emit one `Event` per issue, one per PR, and one per review comment (`source_type: pr_review_comment`), with `parent_event_ids` linking review comments to their PR, and PRs to any issue they close/reference (parse `Closes #123` style links).
- This is where most "discussion" evidence comes from — do not skip review comments, they frequently contain the *actual* rationale that the PR description omits.

### 6.3 ADRs and documentation adapter
- Walk the repo for a conventional ADR directory (`docs/adr/`, `doc/architecture/decisions/`, or configurable path) and parse Markdown ADR files (most follow the Nygard template: Title/Status/Context/Decision/Consequences).
- Parse general docs (Markdown, PDF via a text-extraction library) as `source_type: doc` events. These rarely map to a single decision but often *explain* one — treat them as evidence candidates for the extraction step in §6.4, not as decisions themselves.

### 6.4 Decision extraction (LLM-assisted)
This is the step where the LLM is used — and only this step, plus the explanation-generation step in §9. Everything else in ingestion is deterministic parsing.

- **Input:** a bundle of related events (e.g., an issue thread + the PR that closed it + its review comments + the commits in that PR), retrieved via the entity-resolution links, not just chronological adjacency.
- **Prompt contract:** instruct the model to output *only* structured JSON matching a candidate-decision schema (subset of §5.2, without `decision_id`/`state_history`), and — critically — to only claim a rationale if it can point to a specific `event_id` in the input bundle. Include an explicit instruction: *"If you cannot find clear evidence for why a choice was made, set the decision's confidence low and leave rationale minimal — do not infer motive."*
- **Never let the model free-write prose that gets stored as fact.** Every field the model outputs must resolve back to an `event_id` you already have; the model's job is pattern recognition over evidence you supply, not knowledge synthesis from nothing.
- **Chunking:** for repos with long-running threads, chunk by time window (e.g., issue lifecycle) rather than by token count alone, so a single decision's full context stays in one extraction call.

### 6.5 Identity resolution
Contributors use different handles across Git (`user.email`), GitHub (`login`), and free-text mentions in docs/Slack exports. Build a simple identity-mapping table (`identities`: `canonical_id`, `git_emails[]`, `github_logins[]`, `display_names[]`) seeded manually for the pilot repos (small team, so this is tractable by hand) rather than building an automated identity-resolution ML model — that would be scope creep for a 17-week project.

---

## 7. Entity resolution & the temporal context graph

### 7.1 Entity resolution
- **File/module resolution:** normalize paths (handle renames via Git's rename-detection, `git log --follow`), so a file's history survives a `mv`.
- **Function resolution:** use `pydriller`'s method-level change detection (backed by `lizard` or a language-specific AST parser) to identify when "the same function" is referenced across a commit message, a PR title, and an issue body. Start with exact-name matching within a file; only add fuzzy matching (embedding similarity via `pgvector`) if exact matching proves insufficient in Milestone 2 testing — don't build the harder version first.
- **Dependency resolution:** parse manifest files (`requirements.txt`, `package.json`, etc.) at each commit to track when a dependency was added/removed/version-bumped, and link those commits to any issue/PR that discusses the change.

### 7.2 Building the graph
- Every time a `Decision` is created or an `Event` is ingested, write the corresponding `Entity` and `Edge` rows. This should be a deterministic, testable transformation — not something re-derived ad hoc per query.
- **Edge types and what creates them:**
  - `evidenced_by` (Decision → Event): created at extraction time, one per item in `evidence_event_ids`.
  - `affects` (Decision → Entity): created at extraction time from `artifacts_affected`.
  - `caused_by` (Decision → Decision or Event): when extraction identifies that decision B was made in response to decision/event A.
  - `supersedes` (Decision → Decision): created either by explicit LLM extraction (a PR says "replaces the approach from #45") or by the drift-detection pass in §8.
  - `discussed_in` (Decision → Event): links a decision to *all* related discussion, not just the evidence used for rationale — useful for the Evidence Panel's "show me everything related" view.
  - `conflicts_with` (Decision → Decision): created by reconciliation (§8.1).
  - `drifts_from` (Entity → Decision): created by drift detection (§8.3) — this edge is what routes an item into the review queue.

### 7.3 Querying the graph
Implement three canonical queries early (Milestone 2) since every UI surface in §10 is a view over one of them:
1. **Decision chain for an artifact** — given an `Entity`, return all `Decision`s affecting it, ordered by time, with superseded ones clearly marked (powers the Code-Context View).
2. **Full evidence trail for a decision** — given a `Decision`, return all evidenced_by/discussed_in events (powers the Evidence Panel).
3. **Timeline slice** — given a repo and a time range, return all decisions with state transitions in that window (powers the Project Timeline).

---

## 8. Reconciliation and drift detection

This is the most algorithmically substantial part of the system and the part most likely to be scrutinized as "the non-trivial contribution" — budget real engineering time here, not just LLM prompt-writing.

### 8.1 Conflict detection (contributor/tool disagreement)
- Two `Decision` records are candidates for `conflicts_with` if they affect overlapping `Entity` sets, have overlapping or adjacent time windows, and their `rationale`/`alternatives_considered` are semantically contradictory.
- Implementation: embed each decision's rationale (via the same embedding model used for entity resolution), flag pairs above a similarity threshold on the *entities affected* but with rationale embeddings pointing in different directions (simplest robust approach: ask the LLM to classify a candidate pair as `agree | conflict | unrelated`, given both decisions' full evidence — do not rely on embedding distance alone to declare a conflict, since that produces false positives; use embeddings only to *narrow the candidate pairs*, and the LLM classification, grounded in the evidence, as the final arbiter).
- Every detected conflict goes to the review queue with `confidence` set from the LLM classification step — never auto-resolved.

### 8.2 Supersession detection
- Explicit signal: extraction finds language like "instead of," "replaces," "supersedes #N," "we reverted." Create the `supersedes` edge directly and set the old decision's state to `superseded`.
- Implicit signal: a later decision affects the same `Entity` with contradicting rationale to an earlier `accepted` decision, and no explicit reference exists. Flag as *candidate* supersession → review queue, never auto-applied.

### 8.3 Code-level drift detection
This is the check that runs in CI (per §4), on every merged PR:
1. For every `Entity` touched by the PR, look up the most recent `accepted` `Decision` affecting it.
2. Ask the LLM (given the accepted decision's rationale/constraints and the actual diff) to classify: `consistent | drift | reintroduces_rejected | insufficient_evidence`.
3. If `drift` or `reintroduces_rejected`: create a `drifts_from` edge and push to the review queue with the diff, the original decision, and the LLM's stated reasoning attached as evidence.
4. If `insufficient_evidence`: do **not** guess — mark `unresolved` per the evidence-grounded requirement in §1.5.

**Why this must be evidence-grounded and not a bare LLM opinion:** a false "drift" flag that developers learn to ignore destroys the tool's value faster than a missed one. Every drift flag must carry the specific accepted decision and specific diff lines that triggered it, so a human can verify it in seconds.

---

## 9. Evidence-grounded explanation generation

When a user asks (via the UI) "why does this look like this," the system does **not** make a fresh LLM call over raw repo text. It:
1. Runs the "decision chain for an artifact" query (§7.3.1).
2. Passes the resolved `Decision` objects (which already carry their evidence event IDs) to the LLM purely to *phrase* a readable explanation — the facts come from the graph, not from the model's judgment.
3. Renders the explanation with inline citations back to each `source_url`.
4. If the graph query returns nothing (no decision found for that artifact), the UI must say exactly that — "no recorded decision found for this artifact" — never fabricate a plausible-sounding rationale to fill the gap.

---

## 10. Human review queue

- **What enters the queue:** any `Decision` with `confidence` below a configurable threshold (start at 0.7, tune during Milestone 2 evaluation), any `conflicts_with` edge, and any `drifts_from` edge.
- **Actions available to a reviewer:**
  - `confirm` — accept the extracted record as-is; `review_status → human_confirmed`.
  - `reject` — discard the candidate; `review_status → human_rejected`, and the decision is excluded from all graph queries (soft-deleted, not hard-deleted — keep it for evaluation/audit purposes).
  - `merge` — combine two candidate decisions the system extracted separately but that are actually the same decision; keep one `decision_id`, redirect edges, mark the other `human_rejected` with a pointer to the surviving record.
  - `correct` — edit any field (state, rationale, evidence links) directly; store the correction as a new `state_history`/audit entry, never overwrite silently.
- **Why this queue is a first-class UI surface, not an admin panel bolted on at the end:** it's an explicit required deliverable (§1.6), and it is also your primary source of labeled ground truth for the evaluation pipeline (§12) — every human action here is a data point for measuring extraction accuracy.

---

## 11. Hosted web application — UI specification

Build these six surfaces. Each is a view over a graph query already defined in §7.3 — do not invent new backend logic per screen; the screens are presentation layers over the same underlying model.

1. **Project Timeline** — horizontal time axis; each accepted/rejected/superseded decision as a marker; clicking a marker opens the Decision Explorer for that decision. Filter by entity, contributor, or time range.
2. **Context Graph** — interactive node-link view (via `react-flow`); nodes = decisions/entities/events; edges colored by type (`affects`, `supersedes`, `conflicts_with`, `drifts_from` should be visually distinct, e.g. drift/conflict edges in red). Clicking a node opens its detail panel.
3. **Code-Context View** — user browses/selects a file or function (ideally via a lightweight file-tree, resolved to `Entity` records); shows the full decision chain for that artifact (query §7.3.1), most recent first, each with a one-line "why."
4. **Decision Explorer** — searchable/filterable list of all decisions, faceted by state; each row expands to rationale, alternatives considered (and why rejected), and links to the Evidence Panel.
5. **Evidence Panel** — given a decision, lists every supporting event with a live deep link (`source_url`) to the original commit/issue/PR/comment/doc; this is the panel that makes the "evidence-grounded" requirement inspectable by a human at any time.
6. **Review Queue** — the human-review workflow from §10, as its own page, sorted by confidence ascending (lowest-confidence / most-uncertain items first).

**Onboarding Mode** (from the original report, retained): a guided version of the Project Timeline + Code-Context View aimed at a new contributor — start here if you have time left after the six required surfaces above; it is valuable but not one of the seven hard requirements in §1, so do not let it delay them.

---

## 12. Evaluation pipeline

Build this in parallel with Milestone 1, not as an afterthought in Milestone 3 — you cannot report the required metrics without ground truth that takes time to build.

### 12.1 Ground truth construction
- Pick one team repository (yours) and at least one public repository with rich issues/PRs/commits and either ADRs or detailed documentation (good candidates: projects that maintain an explicit `docs/adr/` folder, or well-documented infra projects with detailed PR discussions).
- Manually label a small set (aim for 30–50 across both repos) of real decisions as `accepted`, `rejected`, or `superseded`, each with the evidence a human found for it. This is your test set — the system's automated extraction is graded against it.

### 12.2 Required metrics (report all of these in Milestone 3)
- **Decision-extraction accuracy** — precision/recall of system-extracted decisions against the manually labeled ground-truth set.
- **Evidence-link accuracy** — of the evidence the system cites, what fraction is actually relevant/correct per human judgment.
- **Contradiction/drift precision** — of the conflicts and drift cases the system flags, what fraction a human confirms as real (this is precision, not recall — recall on drift is much harder to establish and not required).
- **Unsupported-claim rate** — fraction of generated explanations that contain a claim not traceable to a cited event (should be as close to zero as possible; this is the metric that most directly tests the evidence-grounding requirement).
- **Processing latency** — time from a new commit/PR/issue event to it being reflected in the graph and queryable.

### 12.3 Baselines
Run the same test set through, and report comparative numbers against:
- Plain repository/documentation search (e.g., grep or basic full-text search) — the "do nothing" baseline.
- GitHub Copilot's codebase Q&A — ask it the same "why does X look like this" questions and grade its answers by the same rubric.
- Manually maintained ADRs alone (if the public repo has them) — how much of the *actual* decision history do the ADRs capture versus what your system recovers from the full multi-source history.

---

## 13. Database schema (concrete DDL sketch)

```sql
CREATE TABLE events (
  event_id UUID PRIMARY KEY,
  source_type TEXT NOT NULL,
  source_id TEXT NOT NULL,
  source_url TEXT NOT NULL,
  repo TEXT NOT NULL,
  author TEXT,
  ts TIMESTAMPTZ NOT NULL,
  title TEXT,
  body TEXT,
  raw_metadata JSONB,
  UNIQUE (source_type, source_id, repo)
);

CREATE TABLE entities (
  entity_id UUID PRIMARY KEY,
  entity_type TEXT NOT NULL,
  canonical_path TEXT NOT NULL,
  aliases TEXT[] DEFAULT '{}',
  repo TEXT NOT NULL
);

CREATE TABLE decisions (
  decision_id UUID PRIMARY KEY,
  title TEXT NOT NULL,
  state TEXT NOT NULL CHECK (state IN ('proposed','accepted','rejected','superseded','unresolved')),
  made_by TEXT,
  made_at TIMESTAMPTZ,
  rationale TEXT,
  confidence REAL NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'pending_review',
  supersedes_decision_id UUID REFERENCES decisions(decision_id),
  CONSTRAINT evidence_required CHECK (state = 'unresolved' OR confidence IS NOT NULL)
);

CREATE TABLE decision_evidence (
  decision_id UUID REFERENCES decisions(decision_id),
  event_id UUID REFERENCES events(event_id),
  PRIMARY KEY (decision_id, event_id)
);

CREATE TABLE decision_artifacts (
  decision_id UUID REFERENCES decisions(decision_id),
  entity_id UUID REFERENCES entities(entity_id),
  PRIMARY KEY (decision_id, entity_id)
);

CREATE TABLE edges (
  edge_id UUID PRIMARY KEY,
  edge_type TEXT NOT NULL,
  from_id UUID NOT NULL,
  from_type TEXT NOT NULL,
  to_id UUID NOT NULL,
  to_type TEXT NOT NULL,
  valid_from TIMESTAMPTZ NOT NULL,
  valid_to TIMESTAMPTZ
);
```

Enforce `decision_evidence` non-emptiness for non-`unresolved` states at the application layer (Postgres can't easily express "at least one row in a related table" as a column-level CHECK) — write this as a service-layer invariant with a test that tries to violate it and fails.

---

## 14. Seventeen-week execution plan

This maps directly onto the three approved milestones. Treat each week's exit criteria as a go/no-go gate — do not start next week's work if this week's isn't done; slack compounds badly in a 17-week project.

### Milestone 1 — Scope, data, and ground truth (Weeks 1–5)
- **Week 1:** Finalize the event/decision/entity/edge schema (§5, §13). Pick the team repo and the public repo (§12.1 criteria). Set up the repo scaffold, CI skeleton, and Docker Compose dev environment.
- **Week 2:** Build the Git ingestion adapter (§6.1) end-to-end for both repos; verify every emitted event has a valid `source_url`.
- **Week 3:** Build the GitHub Issues/PR/review-comment adapter (§6.2). Build the identity-resolution table (§6.5) for both repos.
- **Week 4:** Build the ADR/docs adapter (§6.3). Begin manual ground-truth labeling (§12.1) in parallel.
- **Week 5:** Finish ground-truth labeling (target 30–50 labeled decisions). Milestone 1 checkpoint: all ingestion adapters idempotent, all events have stable links, ground-truth set complete.

### Milestone 2 — Context engine (Weeks 6–11)
- **Week 6:** Implement entity resolution for files/modules (path normalization, rename tracking).
- **Week 7:** Implement function-level entity resolution and dependency-manifest tracking.
- **Week 8:** Build the LLM-assisted decision extraction pipeline (§6.4) with structured output; run against the pilot repos and manually spot-check outputs against ground truth.
- **Week 9:** Build the temporal context graph write path (§7.2) and the three canonical queries (§7.3).
- **Week 10:** Implement evidence validation, confidence scoring, and conflict detection (§8.1).
- **Week 11:** Implement supersession detection (§8.2) and the first version of code-to-decision drift checks (§8.3). Milestone 2 checkpoint: run the full pipeline against both pilot repos and compute preliminary values for all five required metrics (§12.2), even if rough.

### Milestone 3 — Working prototype (Weeks 12–17)
- **Week 12:** Build the backend API layer (REST endpoints over the three canonical graph queries, plus review-queue actions).
- **Week 13:** Build Project Timeline + Decision Explorer UI surfaces.
- **Week 14:** Build Context Graph + Code-Context View UI surfaces.
- **Week 15:** Build Evidence Panel + Review Queue UI surfaces; wire the GitHub App webhook so new commits/PRs/issues flow through ingestion automatically; wire the CI drift-check job.
- **Week 16:** Run the full evaluation (§12): decision-extraction accuracy, evidence-link accuracy, contradiction/drift precision, unsupported-claim rate, latency — against all three baselines. Demonstrate: (a) one complete chain from discussion → decision → implementation, (b) a real conflicting/superseding decision from another contributor, (c) a controlled change that violates an accepted decision or reintroduces a rejected one, and confirm the system catches it with correct evidence.
- **Week 17:** Finalize the planning-presentation deck content per §15, polish the hosted deployment, freeze for demo, write up final metrics and a clear "here's what each competitor already does vs. what we added" section.

---

## 15. Planning presentation — required content

The presentation is a hosted deliverable (published on the project website), not just slides for class. It must include, explicitly:
1. The exact user problem (use the "new developer can't recover the *why*" framing from §0, grounded in the onboarding/knowledge-transfer research cited in the original report).
2. Data sources (§6).
3. Architecture (§3).
4. Database and graph design (§13, §7).
5. Extraction and linking method (§6.4, §7.1).
6. Baselines (§12.3).
7. Evaluation dataset (§12.1) and metrics (§12.2).
8. Team allocation (§16).
9. Major risks (§17).
10. The complete 17-week execution plan (§14).

---

## 16. Suggested team allocation

Adjust to actual team size, but the work splits naturally into four tracks that can run in parallel after Week 5:
- **Ingestion & entity resolution** (§6, §7.1) — needs someone comfortable with Git internals and the GitHub API.
- **Graph & extraction pipeline** (§7.2–7.3, §8, §9) — needs someone comfortable with LLM prompting/structured output and basic graph algorithms.
- **Backend API & database** (§13, review-queue logic §10) — needs someone comfortable with FastAPI/Postgres.
- **Frontend & hosted deployment** (§11, GitHub App/webhooks, CI integration) — needs someone comfortable with React and basic DevOps.
- **Evaluation & ground truth** (§12) is not a full-time track for one person but a shared responsibility that must start in Week 1 and run continuously — assign an owner who chases labeling and metric computation every week regardless of what else they're doing.

---

## 17. Major risks and mitigations

| Risk | Mitigation |
|---|---|
| LLM extraction hallucinates rationale not actually in the evidence | Enforce the evidence-event-id grounding contract in §6.4/§9 structurally, not just via prompting; measure unsupported-claim rate weekly from Milestone 2 onward, not just at the end |
| Entity resolution across renamed/refactored files breaks decision chains | Use Git's native rename detection (§7.1) from day one; add a regression test with a synthetic rename scenario |
| Drift detection produces too many false positives and gets ignored | Require every drift flag to carry the specific accepted decision + specific diff lines (§8.3); tune the confidence threshold using the ground-truth set before demo |
| 17 weeks is not enough to build ingestion + graph + extraction + drift + full UI | Treat §1's seven required capabilities as the floor and Onboarding Mode / extra UI polish as the ceiling; cut UI polish before cutting any of the seven, since the seven are what's graded |
| Public repo chosen for evaluation turns out to have too little ADR/discussion depth | Vet the candidate public repo in Week 1 by manually checking it has enough decision-worthy history *before* committing to it as the ground-truth source |
| GitHub API rate limits slow ingestion on larger repos | Use GraphQL batching where possible; cache aggressively; for the prototype, scope ingestion to a bounded time window of history rather than the full repo lifetime if needed |

---

## 18. Definition of done for the prototype demo

Before Week 17 ends, verify all of the following are true — this is the actual acceptance checklist, not just a milestone list:

- [ ] All required ingestion sources (§1.1) are wired and idempotent for both pilot repos.
- [ ] Every persisted `Decision` with a non-`unresolved` state has at least one evidence link with a live, clickable `source_url`.
- [ ] The decision lifecycle state machine (§1.2) is enforced in the database and visible in the UI's state-history view.
- [ ] A user can click any code artifact in the Code-Context View and see a correct decision chain.
- [ ] At least one real conflicting/superseding decision from the pilot repos is correctly detected and shown.
- [ ] A controlled, deliberately-introduced violation of an accepted decision is correctly flagged by the CI drift check with correct evidence attached.
- [ ] The Review Queue is functional end-to-end (confirm/reject/merge/correct all work and are reflected in the graph).
- [ ] All five required metrics (§12.2) are computed and reported against all three baselines (§12.3).
- [ ] The hosted app is reachable at a public URL, connected to at least one real repo via the GitHub App/webhook.
- [ ] The planning-presentation content (§15) is published on the project website.

If any box is unchecked, that is the team's actual remaining work — prioritize it over anything not on this list.
