"""
Ground Truth Dataset (Section 12.1)
Contains 30+ curated, manually labeled decisions across both pilot repositories
with known ground truth states, affected artifacts, and verified evidence event IDs.
"""
from typing import List, Dict, Any

GROUND_TRUTH_DATASET: List[Dict[str, Any]] = [
    # --- Pilot Repo 1: acme-eng/thermal-control-system (Decisions 1-16) ---
    {
        "id": "GT_TH_01",
        "repo": "acme-eng/thermal-control-system",
        "title": "Adopt Discrete PID Controller for Chamber Temperature Regulation",
        "expected_state": "accepted",
        "artifact": "src/thermal/control.py::regulate_temperature",
        "expected_evidence_contains": ["evt_adr_thermal_0004", "evt_git_thermal_a1b2c3d4"],
        "has_alternatives": True,
        "is_conflict_target": False
    },
    {
        "id": "GT_TH_02",
        "repo": "acme-eng/thermal-control-system",
        "title": "Reject Simple Deadband Hysteresis for Thermal Control",
        "expected_state": "rejected",
        "artifact": "src/thermal/control.py::regulate_temperature",
        "expected_evidence_contains": ["evt_rev_thermal_comm2"],
        "has_alternatives": True,
        "is_conflict_target": True
    },
    {
        "id": "GT_TH_03",
        "repo": "acme-eng/thermal-control-system",
        "title": "Add Scipy Interpolation for Sensor Curve Calibration",
        "expected_state": "accepted",
        "artifact": "deps::scipy",
        "expected_evidence_contains": ["evt_adr_thermal_0004"],
        "has_alternatives": False,
        "is_conflict_target": False
    },
    {
        "id": "GT_TH_04",
        "repo": "acme-eng/thermal-control-system",
        "title": "Emergency Thermal Cutoff Threshold Set at 95C",
        "expected_state": "accepted",
        "artifact": "src/thermal/control.py",
        "expected_evidence_contains": ["evt_issue_thermal_12"],
        "has_alternatives": False,
        "is_conflict_target": False
    },
    {
        "id": "GT_TH_05",
        "repo": "acme-eng/thermal-control-system",
        "title": "Sample Sensor Bus at 100Hz Hardware Interrupt",
        "expected_state": "accepted",
        "artifact": "src/thermal/control.py::read_telemetry_sensor",
        "expected_evidence_contains": ["evt_git_thermal_a1b2c3d4"],
        "has_alternatives": True,
        "is_conflict_target": False
    },
    {
        "id": "GT_TH_06",
        "repo": "acme-eng/thermal-control-system",
        "title": "Reject Polling-Based Sensor Read Loop in Favor of Interrupts",
        "expected_state": "rejected",
        "artifact": "src/thermal/control.py::read_telemetry_sensor",
        "expected_evidence_contains": ["evt_rev_thermal_comm1"],
        "has_alternatives": True,
        "is_conflict_target": True
    },
    {
        "id": "GT_TH_07",
        "repo": "acme-eng/thermal-control-system",
        "title": "Implement Anti-Windup Clamping on PID Integral Accumulator",
        "expected_state": "accepted",
        "artifact": "src/thermal/control.py::regulate_temperature",
        "expected_evidence_contains": ["evt_adr_thermal_0004"],
        "has_alternatives": False,
        "is_conflict_target": False
    },
    {
        "id": "GT_TH_08",
        "repo": "acme-eng/thermal-control-system",
        "title": "Use Trapezoidal Integration Rule for Error Integration",
        "expected_state": "accepted",
        "artifact": "src/thermal/control.py::regulate_temperature",
        "expected_evidence_contains": ["evt_git_thermal_a1b2c3d4"],
        "has_alternatives": True,
        "is_conflict_target": False
    },
    {
        "id": "GT_TH_09",
        "repo": "acme-eng/thermal-control-system",
        "title": "Reject Euler Forward Difference for Integration (Numerical Instability)",
        "expected_state": "rejected",
        "artifact": "src/thermal/control.py::regulate_temperature",
        "expected_evidence_contains": ["evt_adr_thermal_0004"],
        "has_alternatives": True,
        "is_conflict_target": False
    },
    {
        "id": "GT_TH_10",
        "repo": "acme-eng/thermal-control-system",
        "title": "Calibrate Proportional Gain Kp to 2.4 via Ziegler-Nichols Method",
        "expected_state": "accepted",
        "artifact": "src/thermal/control.py",
        "expected_evidence_contains": ["evt_git_thermal_a1b2c3d4"],
        "has_alternatives": True,
        "is_conflict_target": False
    },
    {
        "id": "GT_TH_11",
        "repo": "acme-eng/thermal-control-system",
        "title": "Reject Manual Gain Tuning in Production Chambers",
        "expected_state": "rejected",
        "artifact": "src/thermal/control.py",
        "expected_evidence_contains": ["evt_rev_thermal_comm2"],
        "has_alternatives": False,
        "is_conflict_target": False
    },
    {
        "id": "GT_TH_12",
        "repo": "acme-eng/thermal-control-system",
        "title": "Store Sensor Calibration Offsets in Non-Volatile EEPROM",
        "expected_state": "accepted",
        "artifact": "src/thermal/control.py",
        "expected_evidence_contains": ["evt_adr_thermal_0004"],
        "has_alternatives": False,
        "is_conflict_target": False
    },
    {
        "id": "GT_TH_13",
        "repo": "acme-eng/thermal-control-system",
        "title": "Telemetry Payload Encoded in Compact Protocol Buffers",
        "expected_state": "accepted",
        "artifact": "src/thermal/control.py",
        "expected_evidence_contains": ["evt_git_thermal_a1b2c3d4"],
        "has_alternatives": True,
        "is_conflict_target": False
    },
    {
        "id": "GT_TH_14",
        "repo": "acme-eng/thermal-control-system",
        "title": "Reject JSON Serialization for 100Hz Telemetry Bus (Bandwidth Limit)",
        "expected_state": "rejected",
        "artifact": "src/thermal/control.py",
        "expected_evidence_contains": ["evt_adr_thermal_0004"],
        "has_alternatives": True,
        "is_conflict_target": False
    },
    {
        "id": "GT_TH_15",
        "repo": "acme-eng/thermal-control-system",
        "title": "Log Critical Thermal Faults to Syslog Ring Buffer",
        "expected_state": "accepted",
        "artifact": "src/thermal/control.py",
        "expected_evidence_contains": ["evt_issue_thermal_12"],
        "has_alternatives": False,
        "is_conflict_target": False
    },
    {
        "id": "GT_TH_16",
        "repo": "acme-eng/thermal-control-system",
        "title": "Reject Synchronous Disk Logging on Real-Time Control Thread",
        "expected_state": "rejected",
        "artifact": "src/thermal/control.py",
        "expected_evidence_contains": ["evt_rev_thermal_comm2"],
        "has_alternatives": True,
        "is_conflict_target": False
    },

    # --- Pilot Repo 2: acme-eng/distributed-cache-service (Decisions 17-32) ---
    {
        "id": "GT_CA_01",
        "repo": "acme-eng/distributed-cache-service",
        "title": "Migrate from In-Memory LRU to Distributed Redis Cluster",
        "expected_state": "accepted",
        "artifact": "src/cache/store.py::cache_get",
        "expected_evidence_contains": ["evt_adr_cache_0009", "evt_rev_cache_c201"],
        "has_alternatives": True,
        "is_conflict_target": True
    },
    {
        "id": "GT_CA_02",
        "repo": "acme-eng/distributed-cache-service",
        "title": "Retain In-Memory LRU Cache with Process Memory Cap",
        "expected_state": "superseded",
        "artifact": "src/cache/store.py::cache_get",
        "expected_evidence_contains": ["evt_pr_cache_38"],
        "has_alternatives": True,
        "is_conflict_target": True
    },
    {
        "id": "GT_CA_03",
        "repo": "acme-eng/distributed-cache-service",
        "title": "Configure Redis Connection Pool with 50 Persistent Connections",
        "expected_state": "accepted",
        "artifact": "src/cache/store.py",
        "expected_evidence_contains": ["evt_adr_cache_0009"],
        "has_alternatives": False,
        "is_conflict_target": False
    },
    {
        "id": "GT_CA_04",
        "repo": "acme-eng/distributed-cache-service",
        "title": "Default Key Expiration TTL Set to 3600 Seconds",
        "expected_state": "accepted",
        "artifact": "src/cache/store.py::cache_set",
        "expected_evidence_contains": ["evt_adr_cache_0009"],
        "has_alternatives": False,
        "is_conflict_target": False
    },
    {
        "id": "GT_CA_05",
        "repo": "acme-eng/distributed-cache-service",
        "title": "Reject Indefinite Key Storage Without Mandatory TTL",
        "expected_state": "rejected",
        "artifact": "src/cache/store.py::cache_set",
        "expected_evidence_contains": ["evt_issue_cache_34"],
        "has_alternatives": True,
        "is_conflict_target": False
    },
    {
        "id": "GT_CA_06",
        "repo": "acme-eng/distributed-cache-service",
        "title": "Deploy Redis Sentinel for High-Availability Automatic Failover",
        "expected_state": "accepted",
        "artifact": "src/cache/store.py",
        "expected_evidence_contains": ["evt_adr_cache_0009"],
        "has_alternatives": True,
        "is_conflict_target": False
    },
    {
        "id": "GT_CA_07",
        "repo": "acme-eng/distributed-cache-service",
        "title": "Reject Standalone Single-Node Redis in Production",
        "expected_state": "rejected",
        "artifact": "src/cache/store.py",
        "expected_evidence_contains": ["evt_adr_cache_0009"],
        "has_alternatives": True,
        "is_conflict_target": False
    },
    {
        "id": "GT_CA_08",
        "repo": "acme-eng/distributed-cache-service",
        "title": "Use Zstandard Compression for Values Larger than 4KB",
        "expected_state": "accepted",
        "artifact": "src/cache/store.py::cache_set",
        "expected_evidence_contains": ["evt_adr_cache_0009"],
        "has_alternatives": True,
        "is_conflict_target": False
    },
    {
        "id": "GT_CA_09",
        "repo": "acme-eng/distributed-cache-service",
        "title": "Reject Gzip Compression Due to High CPU Decompression Latency",
        "expected_state": "rejected",
        "artifact": "src/cache/store.py::cache_set",
        "expected_evidence_contains": ["evt_adr_cache_0009"],
        "has_alternatives": True,
        "is_conflict_target": False
    },
    {
        "id": "GT_CA_10",
        "repo": "acme-eng/distributed-cache-service",
        "title": "Employ Consistent Hashing for Key Sharding Across Nodes",
        "expected_state": "accepted",
        "artifact": "src/cache/store.py",
        "expected_evidence_contains": ["evt_adr_cache_0009"],
        "has_alternatives": True,
        "is_conflict_target": False
    },
    {
        "id": "GT_CA_11",
        "repo": "acme-eng/distributed-cache-service",
        "title": "Reject Modulo-Based Key Partitioning (Causes Massive Cache Misses on Rescaling)",
        "expected_state": "rejected",
        "artifact": "src/cache/store.py",
        "expected_evidence_contains": ["evt_adr_cache_0009"],
        "has_alternatives": True,
        "is_conflict_target": False
    },
    {
        "id": "GT_CA_12",
        "repo": "acme-eng/distributed-cache-service",
        "title": "Implement Probabilistic Early Expiration (XFetch Algorithm) to Prevent Stampedes",
        "expected_state": "accepted",
        "artifact": "src/cache/store.py::cache_get",
        "expected_evidence_contains": ["evt_rev_cache_c201"],
        "has_alternatives": True,
        "is_conflict_target": False
    },
    {
        "id": "GT_CA_13",
        "repo": "acme-eng/distributed-cache-service",
        "title": "Reject Mutex Locking on Cache Miss (Causes Upstream Thread Starvation)",
        "expected_state": "rejected",
        "artifact": "src/cache/store.py::cache_get",
        "expected_evidence_contains": ["evt_rev_cache_c201"],
        "has_alternatives": True,
        "is_conflict_target": False
    },
    {
        "id": "GT_CA_14",
        "repo": "acme-eng/distributed-cache-service",
        "title": "Track Cache Hit/Miss Telemetry via Prometheus Counters",
        "expected_state": "accepted",
        "artifact": "src/cache/store.py",
        "expected_evidence_contains": ["evt_pr_cache_38"],
        "has_alternatives": False,
        "is_conflict_target": False
    },
    {
        "id": "GT_CA_15",
        "repo": "acme-eng/distributed-cache-service",
        "title": "Graceful Fallback to Direct Database Read on Redis Timeout",
        "expected_state": "accepted",
        "artifact": "src/cache/store.py::cache_get",
        "expected_evidence_contains": ["evt_adr_cache_0009"],
        "has_alternatives": False,
        "is_conflict_target": False
    },
    {
        "id": "GT_CA_16",
        "repo": "acme-eng/distributed-cache-service",
        "title": "Reject Hard Exception Throws on Cache Unavailability",
        "expected_state": "rejected",
        "artifact": "src/cache/store.py::cache_get",
        "expected_evidence_contains": ["evt_adr_cache_0009"],
        "has_alternatives": True,
        "is_conflict_target": False
    }
]
