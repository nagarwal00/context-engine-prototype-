"""
Pilot Repositories and Seed Data Generator (Section 12.1 & 14)
Populates realistic multi-source histories for:
1. acme-eng/thermal-control-system (PID vs bang-bang, overheating incident, drift test)
2. acme-eng/distributed-cache-service (LRU vs Redis, contributor conflict, memory leak)
"""
from backend.db import Database
from backend.models import Event, Decision, Entity, Edge
from backend.ingestion.identity import IdentityResolver
from backend.engine.entity_res import EntityResolver
from backend.engine.graph import TemporalGraph
from backend.engine.reconciliation import ReconciliationEngine
from backend.engine.drift_detector import DriftDetector

def populate_seed_data(db: Database):
    # Clear existing data for a clean, deterministic run
    with db.get_connection() as conn:
        conn.execute("DELETE FROM guard_rules")
        conn.execute("DELETE FROM state_history")
        conn.execute("DELETE FROM edges")
        conn.execute("DELETE FROM decision_evidence")
        conn.execute("DELETE FROM decision_artifacts")
        conn.execute("DELETE FROM decisions")
        conn.execute("DELETE FROM entities")
        conn.execute("DELETE FROM events")
        conn.commit()

    ident_resolver = IdentityResolver(db)
    ent_resolver = EntityResolver(db)
    graph = TemporalGraph(db)

    # =========================================================================
    # REPOSITORY 1: acme-eng/thermal-control-system
    # =========================================================================
    repo1 = "acme-eng/thermal-control-system"

    # Entities for Repo 1
    e1_file = ent_resolver.resolve_file_entity(repo1, "src/thermal/control.py", "Core thermal regulation module")
    e1_fn_regulate = ent_resolver.resolve_function_entity(repo1, "src/thermal/control.py", "regulate_temperature", "Applies feedback loop control algorithm")
    e1_fn_sensor = ent_resolver.resolve_function_entity(repo1, "src/thermal/control.py", "read_telemetry_sensor", "Reads raw temperature sensor hardware bus")
    e1_adr_file = ent_resolver.resolve_file_entity(repo1, "docs/adr/0004-pid-thermal-regulation.md", "ADR 0004 documentation")
    e1_dep_scipy = ent_resolver.resolve_dependency_entity(repo1, "scipy", "==1.11.2")

    # Events for Repo 1
    # 1. Issue 12: Overheating bug in v1
    ev_issue_12 = Event(
        event_id="evt_issue_thermal_12",
        source_type="github_issue",
        source_id="12",
        source_url=f"https://github.com/{repo1}/issues/12",
        repo=repo1,
        author="alex_rodriguez",
        timestamp="2026-01-10T09:15:00Z",
        title="#12: Severe chamber overheating observed under 80% duty cycle",
        body="During long thermal chamber runs, temperature oscillated wildly between 65C and 94C with bang-bang hysteresis. Overheating threshold triggered emergency shutdown 4 times.",
        artifacts_touched=["src/thermal/control.py"]
    )
    db.upsert_event(ev_issue_12)

    # 2. Discussion on Issue 12: Approach B proposed (hysteresis tuning)
    ev_issue_12_comm = Event(
        event_id="evt_rev_thermal_comm1",
        source_type="pr_review_comment",
        source_id="c101",
        source_url=f"https://github.com/{repo1}/issues/12#issuecomment-101",
        repo=repo1,
        author="marcus_vance",
        timestamp="2026-01-11T11:20:00Z",
        title="Marcus on Issue #12: Proposed deadband tuning",
        body="We could tighten the deadband on the simple threshold on-off controller to +/- 1.5C. That requires zero external math libraries.",
        artifacts_touched=["src/thermal/control.py"],
        parent_event_ids=["evt_issue_thermal_12"]
    )
    db.upsert_event(ev_issue_12_comm)

    # 3. Discussion on Issue 12: Approach B rejected by Sarah due to latency/overshoot
    ev_issue_12_sarah = Event(
        event_id="evt_rev_thermal_comm2",
        source_type="pr_review_comment",
        source_id="c102",
        source_url=f"https://github.com/{repo1}/issues/12#issuecomment-102",
        repo=repo1,
        author="sarah_chen",
        timestamp="2026-01-12T14:45:00Z",
        title="Sarah on Issue #12: Benchmark results against deadband tuning",
        body="I benchmarked deadband tuning in simulation. It increased latency by 17% and still caused a 6.2C overshoot on rapid thermal transient. We must reject on-off hysteresis and move to continuous PID control.",
        artifacts_touched=["src/thermal/control.py"],
        parent_event_ids=["evt_issue_thermal_12"]
    )
    db.upsert_event(ev_issue_12_sarah)

    # 4. ADR 0004 Markdown
    ev_adr_4 = Event(
        event_id="evt_adr_thermal_0004",
        source_type="adr",
        source_id="docs/adr/0004-pid-thermal-regulation.md",
        source_url=f"https://github.com/{repo1}/blob/main/docs/adr/0004-pid-thermal-regulation.md",
        repo=repo1,
        author="sarah_chen",
        timestamp="2026-01-15T16:00:00Z",
        title="ADR 0004: Adopt Discrete PID Algorithm for Thermal Regulation",
        body="""Status: accepted

Context:
Previous bang-bang / on-off controller caused severe thermal oscillations and triggered chamber shutdown (Issue #12). Deadband tuning was tested and rejected because it increased control latency by 17% and failed transient tests.

Decision:
Implement discrete PID control with anti-windup clamping in regulate_temperature(). Use scipy interpolation for telemetry curve smoothing.

Consequences:
- Smooth thermal trajectory within +/- 0.4C of setpoint.
- Added dependency on scipy.
- Slightly higher CPU compute per control cycle.""",
        artifacts_touched=["src/thermal/control.py", "docs/adr/0004-pid-thermal-regulation.md"],
        raw_metadata={"parsed_adr": {
            "title": "Adopt Discrete PID Algorithm for Thermal Regulation",
            "status": "accepted",
            "context": "Previous bang-bang / on-off controller caused severe thermal oscillations. Deadband tuning increased latency by 17%.",
            "decision": "Implement discrete PID control with anti-windup clamping in regulate_temperature().",
            "consequences": "Maintains temperature within +/- 0.4C setpoint with anti-windup."
        }}
    )
    db.upsert_event(ev_adr_4)

    # 5. Commit implementing PID in control.py
    ev_commit_pid = Event(
        event_id="evt_git_thermal_a1b2c3d4",
        source_type="git_commit",
        source_id="a1b2c3d4e5f67890",
        source_url=f"https://github.com/{repo1}/commit/a1b2c3d4e5f67890",
        repo=repo1,
        author="sarah_chen",
        timestamp="2026-01-18T10:00:00Z",
        title="feat(thermal): implement discrete PID controller with anti-windup (Closes #12)",
        body="Replaces on-off controller with discrete PID controller. Implements ADR 0004. Closes #12.",
        artifacts_touched=["src/thermal/control.py", "requirements.txt"],
        parent_event_ids=["evt_issue_thermal_12"],
        raw_metadata={
            "diff_summary": "@@ -14,6 +14,24 @@ def regulate_temperature(current_temp, target_temp):\n- if current_temp > target_temp: fan_on()\n+ error = target_temp - current_temp\n+ p_term = Kp * error\n+ i_term = Ki * (integral + error * dt)\n+ output = clamp(p_term + i_term + d_term, 0.0, 100.0)"
        }
    )
    db.upsert_event(ev_commit_pid)

    # Decisions for Repo 1:
    # Decision 1.1: Rejected Deadband Tuning
    dec_deadband = Decision(
        decision_id="dec_thermal_deadband_rejected",
        title="Reject Simple Deadband Hysteresis for Thermal Control",
        state="rejected",
        made_by="sarah_chen",
        made_at="2026-01-12T15:00:00Z",
        artifacts_affected=[e1_file.entity_id, e1_fn_regulate.entity_id],
        alternatives_considered=[{
            "description": "Deadband on-off threshold control +/- 1.5C",
            "rejection_reason": "Benchmarking revealed 17% higher latency and persistent 6.2C transient overshoot",
            "evidence_event_ids": [ev_issue_12_sarah.event_id]
        }],
        rationale="Tested in simulation following Issue #12; deadband was insufficient to prevent emergency chamber thermal trip.",
        evidence_event_ids=[ev_issue_12_sarah.event_id, ev_issue_12_comm.event_id],
        confidence=0.96,
        review_status="auto_confirmed",
        repo=repo1
    )
    db.save_decision(dec_deadband)
    graph.link_decision_to_artifacts_and_evidence(dec_deadband)

    # Decision 1.2: Accepted PID Controller (ADR 0004)
    dec_pid = Decision(
        decision_id="dec_thermal_pid_accepted",
        title="Adopt Discrete PID Controller for Chamber Temperature Regulation",
        state="accepted",
        made_by="sarah_chen",
        made_at="2026-01-15T16:00:00Z",
        artifacts_affected=[e1_file.entity_id, e1_fn_regulate.entity_id, e1_dep_scipy.entity_id],
        alternatives_considered=[{
            "description": "On-off hysteresis deadband controller",
            "rejection_reason": "Caused 17% latency increase and 6.2C overshoot in thermal transient tests",
            "evidence_event_ids": [ev_issue_12_sarah.event_id]
        }],
        rationale="ADR 0004: Continuous PID loop with anti-windup clamping guarantees stability within +/- 0.4C of setpoint under heavy duty cycle.",
        evidence_event_ids=[ev_adr_4.event_id, ev_commit_pid.event_id],
        confidence=0.98,
        review_status="auto_confirmed",
        repo=repo1
    )
    db.save_decision(dec_pid)
    graph.link_decision_to_artifacts_and_evidence(dec_pid)

    # =========================================================================
    # REPOSITORY 2: acme-eng/distributed-cache-service
    # =========================================================================
    repo2 = "acme-eng/distributed-cache-service"

    e2_file = ent_resolver.resolve_file_entity(repo2, "src/cache/store.py", "Distributed caching implementation")
    e2_fn_get = ent_resolver.resolve_function_entity(repo2, "src/cache/store.py", "cache_get", "Fetch key from cache cluster")
    e2_fn_set = ent_resolver.resolve_function_entity(repo2, "src/cache/store.py", "cache_set", "Write key-value pair to cluster with TTL")
    e2_dep_redis = ent_resolver.resolve_dependency_entity(repo2, "redis", "==4.5.4")

    # Events for Repo 2
    # 1. Issue 34: Out of memory crash with local LRU dict cache
    ev_issue_34 = Event(
        event_id="evt_issue_cache_34",
        source_type="github_issue",
        source_id="34",
        source_url=f"https://github.com/{repo2}/issues/34",
        repo=repo2,
        author="alex_rodriguez",
        timestamp="2026-02-01T10:00:00Z",
        title="#34: Worker node OOMKilled under 50,000 req/sec spike",
        body="Production instances running the in-memory Python LRU cache exceeded 8GB RAM and were OOMKilled by Kubernetes during flash sale.",
        artifacts_touched=["src/cache/store.py"]
    )
    db.upsert_event(ev_issue_34)

    # 2. PR 38: Marcus Vance submits PR to upgrade in-memory cache with memory limits
    ev_pr_38 = Event(
        event_id="evt_pr_cache_38",
        source_type="github_pr",
        source_id="38",
        source_url=f"https://github.com/{repo2}/pull/38",
        repo=repo2,
        author="marcus_vance",
        timestamp="2026-02-03T14:30:00Z",
        title="PR #38: Add soft memory cap to in-memory LRU cache (Closes #34)",
        body="Adds a maximum memory threshold to local Python process memory before aggressive eviction. Keeps caching local with sub-millisecond access.",
        artifacts_touched=["src/cache/store.py"],
        parent_event_ids=["evt_issue_cache_34"]
    )
    db.upsert_event(ev_pr_38)

    # 3. Review Comment on PR 38: Priya Patel disagrees and advocates Redis cluster
    ev_pr_38_priya = Event(
        event_id="evt_rev_cache_c201",
        source_type="pr_review_comment",
        source_id="c201",
        source_url=f"https://github.com/{repo2}/pull/38#discussion_r201",
        repo=repo2,
        author="priya_patel",
        timestamp="2026-02-04T09:00:00Z",
        title="Priya review on PR #38: In-memory cache cannot scale across replicas",
        body="Local LRU will never solve cache stampedes across multiple container replicas. Each pod will maintain cold caches. We need a distributed Redis cluster.",
        artifacts_touched=["src/cache/store.py"],
        parent_event_ids=["evt_pr_cache_38"]
    )
    db.upsert_event(ev_pr_38_priya)

    # 4. ADR 0009: Move to Redis Cluster
    ev_adr_9 = Event(
        event_id="evt_adr_cache_0009",
        source_type="adr",
        source_id="docs/adr/0009-redis-cluster-cache.md",
        source_url=f"https://github.com/{repo2}/blob/main/docs/adr/0009-redis-cluster-cache.md",
        repo=repo2,
        author="priya_patel",
        timestamp="2026-02-06T15:00:00Z",
        title="ADR 0009: Migrate to Redis Cluster for Distributed Caching",
        body="""Status: accepted

Context:
In-memory LRU caching caused node OOM crashes (#34) and replica cache incoherence. PR #38 attempted local memory capping but was rejected because container autoscaling requires shared cache state.

Decision:
Decommission in-memory LRU dict in store.py and implement Redis cluster client with sentinel failover and connection pooling.

Consequences:
- Resilient distributed cache state across all container instances.
- Solves memory leak and OOM termination.
- Network overhead ~1.2ms per roundtrip.""",
        artifacts_touched=["src/cache/store.py", "docs/adr/0009-redis-cluster-cache.md"],
        raw_metadata={"parsed_adr": {
            "title": "Migrate to Redis Cluster for Distributed Caching",
            "status": "accepted",
            "context": "Local in-memory cache caused OOM crashes. Local memory capping cannot sync across pods.",
            "decision": "Decommission in-memory cache and migrate to Redis cluster.",
            "consequences": "Resilient cache state across all pods; solves OOM crashes."
        }}
    )
    db.upsert_event(ev_adr_9)

    # Decisions for Repo 2:
    # Decision 2.1: Proposed / Contradictory Local LRU Memory Cap (Marcus Vance)
    dec_lru_cap = Decision(
        decision_id="dec_cache_local_lru_proposed",
        title="Retain In-Memory LRU Cache with Process Memory Cap",
        state="proposed",
        made_by="marcus_vance",
        made_at="2026-02-03T14:30:00Z",
        artifacts_affected=[e2_file.entity_id, e2_fn_get.entity_id, e2_fn_set.entity_id],
        alternatives_considered=[{
            "description": "Redis cluster deployment",
            "rejection_reason": "Adds operational complexity and 1-2ms network hop over in-process memory",
            "evidence_event_ids": [ev_pr_38.event_id]
        }],
        rationale="Keep cache strictly inside Python heap to guarantee sub-millisecond access and avoid external Redis infra.",
        evidence_event_ids=[ev_pr_38.event_id],
        confidence=0.82,
        review_status="pending_review",
        repo=repo2
    )
    db.save_decision(dec_lru_cap)
    graph.link_decision_to_artifacts_and_evidence(dec_lru_cap)

    # Marcus's proposal is accepted on 2026-02-04
    from backend.engine.lifecycle import transition
    transition(
        db,
        dec_lru_cap.decision_id,
        "accepted",
        actor="marcus_vance",
        reason="Accepted temporary in-memory LRU cache with soft memory cap",
        at="2026-02-04T10:00:00Z"
    )

    # Decision 2.2: Accepted Redis Cluster (Priya Patel, superseding Marcus's proposal)
    dec_redis = Decision(
        decision_id="dec_cache_redis_accepted",
        title="Migrate from In-Memory LRU to Distributed Redis Cluster",
        state="accepted",
        made_by="priya_patel",
        made_at="2026-02-06T15:00:00Z",
        artifacts_affected=[e2_file.entity_id, e2_fn_get.entity_id, e2_fn_set.entity_id, e2_dep_redis.entity_id],
        alternatives_considered=[{
            "description": "In-memory LRU cache with soft memory cap (PR #38)",
            "rejection_reason": "Rejected: Local cache causes cache stampedes and memory duplication across container replicas",
            "evidence_event_ids": [ev_pr_38_priya.event_id]
        }],
        rationale="ADR 0009: Decommission local in-memory dict and migrate to Redis cluster to prevent container OOMs and maintain cache consistency across autoscaled pods.",
        evidence_event_ids=[ev_adr_9.event_id, ev_pr_38_priya.event_id],
        supersedes_decision_id=dec_lru_cap.decision_id,
        confidence=0.97,
        review_status="auto_confirmed",
        repo=repo2
    )
    db.save_decision(dec_redis)
    graph.link_decision_to_artifacts_and_evidence(dec_redis)

    # Mark supersession via lifecycle transition engine
    transition(
        db,
        dec_lru_cap.decision_id,
        "superseded",
        actor="priya_patel",
        reason="ADR 0009: Migrated from in-memory cache to distributed Redis cluster",
        at=dec_redis.made_at,
        superseded_by_id=dec_redis.decision_id
    )

    # Create explicit conflict between Marcus's proposal and Priya's Redis decision
    graph.add_edge(
        edge_type="conflicts_with",
        from_id=dec_lru_cap.decision_id,
        from_type="decision",
        to_id=dec_redis.decision_id,
        to_type="decision",
        valid_from=dec_redis.made_at
    )

    # Propose Decision Guard Rules (Section 5 Novelty Feature)
    from backend.engine.guard_rules import propose_rules_from_decision
    for d in [dec_deadband, dec_pid, dec_lru_cap, dec_redis]:
        for rule in propose_rules_from_decision(d):
            db.upsert_guard_rule(rule)

    # =========================================================================
    # CONTROLLED DRIFT SCENARIO (Section 8.3 & Milestone 3)
    # A PR diff that deliberately reintroduces the rejected on-off threshold control
    # =========================================================================
    drift_detector = DriftDetector(db)
    simulated_violating_diff = """
    @@ -25,12 +25,8 @@ def regulate_temperature(current_temp, target_temp):
    -    error = target_temp - current_temp
    -    p_term = self.Kp * error
    -    i_term = self.Ki * self.integral
    -    return self.clamp(p_term + i_term, 0.0, 100.0)
    +    # Quick hack: bypass PID controller and use simple threshold on_off hysteresis
    +    if current_temp > target_temp + 1.5:
    +        return 0.0
    +    return 100.0
    """
    drift_report = drift_detector.analyze_diff_for_drift(
        repo=repo1,
        commit_or_pr_id="pr_thermal_violation_44",
        author="elena_rostova",
        changed_files=["src/thermal/control.py"],
        diff_text=simulated_violating_diff
    )
    drift_results = drift_report["findings"] if isinstance(drift_report, dict) else drift_report

    return {
        "repo1": repo1,
        "repo2": repo2,
        "drift_cases_detected": len(drift_results)
    }
