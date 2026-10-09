"""
Synthetic Pilot Ground Truth Dataset (Smoke Test)
NOTE: This dataset represents the synthetic pilot repositories used strictly for
pipeline smoke testing and integration verification (acme-eng/thermal-control-system
and acme-eng/distributed-cache-service).
Headline evaluation is performed on real repositories in WhyBench (Phase 2).
"""
from typing import List, Dict, Any

# Synthetic pilot ground truth dataset (smoke test)
PILOT_GROUND_TRUTH_DATASET: List[Dict[str, Any]] = [
    {
        "id": "PILOT_GT_TH_01",
        "repo": "acme-eng/thermal-control-system",
        "title": "Adopt Discrete PID Controller for Chamber Temperature Regulation",
        "expected_state": "accepted",
        "artifact": "src/thermal/control.py::regulate_temperature",
        "expected_evidence_contains": ["evt_adr_thermal_0004", "evt_git_thermal_a1b2c3d4"],
        "has_alternatives": True,
        "is_conflict_target": False
    },
    {
        "id": "PILOT_GT_TH_02",
        "repo": "acme-eng/thermal-control-system",
        "title": "Reject Simple Deadband Hysteresis for Thermal Control",
        "expected_state": "rejected",
        "artifact": "src/thermal/control.py::regulate_temperature",
        "expected_evidence_contains": ["evt_issue_thermal_12_sarah", "evt_issue_thermal_12_comm"],
        "has_alternatives": True,
        "is_conflict_target": True
    },
    {
        "id": "PILOT_GT_CACHE_01",
        "repo": "acme-eng/distributed-cache-service",
        "title": "Migrate from In-Memory LRU to Distributed Redis Cluster",
        "expected_state": "accepted",
        "artifact": "src/cache/store.py::cache_get",
        "expected_evidence_contains": ["evt_adr_cache_0009", "evt_rev_cache_c201"],
        "has_alternatives": True,
        "is_conflict_target": False
    },
    {
        "id": "PILOT_GT_CACHE_02",
        "repo": "acme-eng/distributed-cache-service",
        "title": "Retain In-Memory LRU Cache with Process Memory Cap",
        "expected_state": "rejected",
        "artifact": "src/cache/store.py::cache_get",
        "expected_evidence_contains": ["evt_pr_cache_38"],
        "has_alternatives": True,
        "is_conflict_target": True
    }
]

# Aliased for backward compatibility with existing imports
GROUND_TRUTH_DATASET = PILOT_GROUND_TRUTH_DATASET
