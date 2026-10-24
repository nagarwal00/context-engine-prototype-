// Auto-generated static dataset for GitHub Pages deployment
window.__CIF_STATIC_DATA__ = {
  "database": "context_intelligence.db",
  "db_snapshot_sha256": "ec7e62cd3c0bba7fb9dd4f195355490a05e718a0389a0df8cf210b96aa3715ba",
  "endpoints": {
    "artifacts_all": {
      "data": [
        {
          "aliases": [
            "redis ==4.5.4",
            "redis"
          ],
          "canonical_path": "deps::redis",
          "current_state_summary": "Dependency package redis (==4.5.4)",
          "decision_count": 1,
          "entity_id": "ent_dep_acme-eng_distributed-cache-service_redis",
          "entity_type": "dependency",
          "repo": "acme-eng/distributed-cache-service",
          "repo_full_name": "acme-eng/distributed-cache-service"
        },
        {
          "aliases": [
            "scipy ==1.11.2",
            "scipy"
          ],
          "canonical_path": "deps::scipy",
          "current_state_summary": "Dependency package scipy (==1.11.2)",
          "decision_count": 1,
          "entity_id": "ent_dep_acme-eng_thermal-control-system_scipy",
          "entity_type": "dependency",
          "repo": "acme-eng/thermal-control-system",
          "repo_full_name": "acme-eng/thermal-control-system"
        },
        {
          "aliases": [
            "docs/adr/0004-pid-thermal-regulation.md",
            "0004-pid-thermal-regulation.md"
          ],
          "canonical_path": "docs/adr/0004-pid-thermal-regulation.md",
          "current_state_summary": "ADR 0004 documentation",
          "decision_count": 0,
          "entity_id": "ent_file_acme-eng_thermal-control-system_docs_adr_0004-pid-thermal-regulation_md",
          "entity_type": "file",
          "repo": "acme-eng/thermal-control-system",
          "repo_full_name": "acme-eng/thermal-control-system"
        },
        {
          "aliases": [
            "src/cache/store.py",
            "store.py"
          ],
          "canonical_path": "src/cache/store.py",
          "current_state_summary": "Distributed caching implementation",
          "decision_count": 2,
          "entity_id": "ent_file_acme-eng_distributed-cache-service_src_cache_store_py",
          "entity_type": "file",
          "repo": "acme-eng/distributed-cache-service",
          "repo_full_name": "acme-eng/distributed-cache-service"
        },
        {
          "aliases": [
            "src/thermal/control.py",
            "control.py"
          ],
          "canonical_path": "src/thermal/control.py",
          "current_state_summary": "Core thermal regulation module",
          "decision_count": 2,
          "entity_id": "ent_file_acme-eng_thermal-control-system_src_thermal_control_py",
          "entity_type": "file",
          "repo": "acme-eng/thermal-control-system",
          "repo_full_name": "acme-eng/thermal-control-system"
        },
        {
          "aliases": [
            "store.py::cache_get",
            "cache_get"
          ],
          "canonical_path": "src/cache/store.py::cache_get",
          "current_state_summary": "Fetch key from cache cluster",
          "decision_count": 2,
          "entity_id": "ent_fn_acme-eng_distributed-cache-service_src_cache_store_py_cache_get",
          "entity_type": "function",
          "repo": "acme-eng/distributed-cache-service",
          "repo_full_name": "acme-eng/distributed-cache-service"
        },
        {
          "aliases": [
            "store.py::cache_set",
            "cache_set"
          ],
          "canonical_path": "src/cache/store.py::cache_set",
          "current_state_summary": "Write key-value pair to cluster with TTL",
          "decision_count": 2,
          "entity_id": "ent_fn_acme-eng_distributed-cache-service_src_cache_store_py_cache_set",
          "entity_type": "function",
          "repo": "acme-eng/distributed-cache-service",
          "repo_full_name": "acme-eng/distributed-cache-service"
        },
        {
          "aliases": [
            "control.py::read_telemetry_sensor",
            "read_telemetry_sensor"
          ],
          "canonical_path": "src/thermal/control.py::read_telemetry_sensor",
          "current_state_summary": "Reads raw temperature sensor hardware bus",
          "decision_count": 0,
          "entity_id": "ent_fn_acme-eng_thermal-control-system_src_thermal_control_py_read_telemetry_sensor",
          "entity_type": "function",
          "repo": "acme-eng/thermal-control-system",
          "repo_full_name": "acme-eng/thermal-control-system"
        },
        {
          "aliases": [
            "control.py::regulate_temperature",
            "regulate_temperature"
          ],
          "canonical_path": "src/thermal/control.py::regulate_temperature",
          "current_state_summary": "Applies feedback loop control algorithm",
          "decision_count": 2,
          "entity_id": "ent_fn_acme-eng_thermal-control-system_src_thermal_control_py_regulate_temperature",
          "entity_type": "function",
          "repo": "acme-eng/thermal-control-system",
          "repo_full_name": "acme-eng/thermal-control-system"
        }
      ],
      "status": "success"
    },
    "artifacts_cache": {
      "data": [
        {
          "aliases": [
            "redis ==4.5.4",
            "redis"
          ],
          "canonical_path": "deps::redis",
          "current_state_summary": "Dependency package redis (==4.5.4)",
          "decision_count": 1,
          "entity_id": "ent_dep_acme-eng_distributed-cache-service_redis",
          "entity_type": "dependency",
          "repo": "acme-eng/distributed-cache-service",
          "repo_full_name": "acme-eng/distributed-cache-service"
        },
        {
          "aliases": [
            "src/cache/store.py",
            "store.py"
          ],
          "canonical_path": "src/cache/store.py",
          "current_state_summary": "Distributed caching implementation",
          "decision_count": 2,
          "entity_id": "ent_file_acme-eng_distributed-cache-service_src_cache_store_py",
          "entity_type": "file",
          "repo": "acme-eng/distributed-cache-service",
          "repo_full_name": "acme-eng/distributed-cache-service"
        },
        {
          "aliases": [
            "store.py::cache_get",
            "cache_get"
          ],
          "canonical_path": "src/cache/store.py::cache_get",
          "current_state_summary": "Fetch key from cache cluster",
          "decision_count": 2,
          "entity_id": "ent_fn_acme-eng_distributed-cache-service_src_cache_store_py_cache_get",
          "entity_type": "function",
          "repo": "acme-eng/distributed-cache-service",
          "repo_full_name": "acme-eng/distributed-cache-service"
        },
        {
          "aliases": [
            "store.py::cache_set",
            "cache_set"
          ],
          "canonical_path": "src/cache/store.py::cache_set",
          "current_state_summary": "Write key-value pair to cluster with TTL",
          "decision_count": 2,
          "entity_id": "ent_fn_acme-eng_distributed-cache-service_src_cache_store_py_cache_set",
          "entity_type": "function",
          "repo": "acme-eng/distributed-cache-service",
          "repo_full_name": "acme-eng/distributed-cache-service"
        }
      ],
      "status": "success"
    },
    "artifacts_thermal": {
      "data": [
        {
          "aliases": [
            "scipy ==1.11.2",
            "scipy"
          ],
          "canonical_path": "deps::scipy",
          "current_state_summary": "Dependency package scipy (==1.11.2)",
          "decision_count": 1,
          "entity_id": "ent_dep_acme-eng_thermal-control-system_scipy",
          "entity_type": "dependency",
          "repo": "acme-eng/thermal-control-system",
          "repo_full_name": "acme-eng/thermal-control-system"
        },
        {
          "aliases": [
            "docs/adr/0004-pid-thermal-regulation.md",
            "0004-pid-thermal-regulation.md"
          ],
          "canonical_path": "docs/adr/0004-pid-thermal-regulation.md",
          "current_state_summary": "ADR 0004 documentation",
          "decision_count": 0,
          "entity_id": "ent_file_acme-eng_thermal-control-system_docs_adr_0004-pid-thermal-regulation_md",
          "entity_type": "file",
          "repo": "acme-eng/thermal-control-system",
          "repo_full_name": "acme-eng/thermal-control-system"
        },
        {
          "aliases": [
            "src/thermal/control.py",
            "control.py"
          ],
          "canonical_path": "src/thermal/control.py",
          "current_state_summary": "Core thermal regulation module",
          "decision_count": 2,
          "entity_id": "ent_file_acme-eng_thermal-control-system_src_thermal_control_py",
          "entity_type": "file",
          "repo": "acme-eng/thermal-control-system",
          "repo_full_name": "acme-eng/thermal-control-system"
        },
        {
          "aliases": [
            "control.py::read_telemetry_sensor",
            "read_telemetry_sensor"
          ],
          "canonical_path": "src/thermal/control.py::read_telemetry_sensor",
          "current_state_summary": "Reads raw temperature sensor hardware bus",
          "decision_count": 0,
          "entity_id": "ent_fn_acme-eng_thermal-control-system_src_thermal_control_py_read_telemetry_sensor",
          "entity_type": "function",
          "repo": "acme-eng/thermal-control-system",
          "repo_full_name": "acme-eng/thermal-control-system"
        },
        {
          "aliases": [
            "control.py::regulate_temperature",
            "regulate_temperature"
          ],
          "canonical_path": "src/thermal/control.py::regulate_temperature",
          "current_state_summary": "Applies feedback loop control algorithm",
          "decision_count": 2,
          "entity_id": "ent_fn_acme-eng_thermal-control-system_src_thermal_control_py_regulate_temperature",
          "entity_type": "function",
          "repo": "acme-eng/thermal-control-system",
          "repo_full_name": "acme-eng/thermal-control-system"
        }
      ],
      "status": "success"
    },
    "benchmark": {
      "data": {
        "baselines": {
          "baseline_copilot": {
            "decision_recall": "not measured",
            "evaluated_samples": 0,
            "hallucination_rate": "not measured",
            "name": "Baseline D: GitHub Copilot",
            "status": "not measured"
          },
          "baseline_docs_only": {
            "decision_recall": 50.0,
            "found_count": 2,
            "name": "Baseline B: Documentation/ADRs Only",
            "note": "Task 1 (Evidence Retrieval) only; Task 2 (Decision Reconstruction) is n/a.",
            "status": "measured",
            "task_1_applicable": true,
            "task_1_hit_rate": 50.0,
            "task_1_top_k": 5,
            "task_2_applicable": false,
            "task_2_decision_recall": "n/a",
            "task_2_refusal_accuracy": "n/a (always answers)",
            "task_2_state_accuracy": "n/a",
            "top_k": 5,
            "total_count": 4
          },
          "baseline_keyword": {
            "decision_recall": 75.0,
            "found_count": 3,
            "name": "Baseline A: Keyword Search (Grep/BM25)",
            "note": "Task 1 (Evidence Retrieval) only; Task 2 (Decision Reconstruction) is n/a.",
            "status": "measured",
            "task_1_applicable": true,
            "task_1_hit_rate": 75.0,
            "task_1_top_k": 5,
            "task_2_applicable": false,
            "task_2_decision_recall": "n/a",
            "task_2_refusal_accuracy": "n/a (always answers)",
            "task_2_state_accuracy": "n/a",
            "top_k": 5,
            "total_count": 4
          },
          "baseline_llm": {
            "decision_recall": "not measured",
            "evidence_grounding_accuracy": "not measured",
            "name": "Baseline C: Plain LLM Q&A",
            "note": "Requires CIF_LLM_API_KEY and CIF_LLM_MODEL environment variables",
            "status": "not measured"
          }
        },
        "conflict_evaluation": {
          "fn": 0,
          "fp": 0,
          "precision": 100.0,
          "recall": 100.0,
          "status": "measured",
          "tn": 3,
          "total_cases": 7,
          "tp": 4
        },
        "details": {
          "found": [
            {
              "decision_id": "dec_cache_redis_accepted",
              "expected_state": "accepted",
              "gt_id": "PILOT_GT_CACHE_01",
              "gt_title": "Migrate from In-Memory LRU to Distributed Redis Cluster",
              "overlap_count": 2,
              "shared_events": [
                "evt_adr_cache_0009",
                "evt_rev_cache_c201"
              ],
              "system_state": "accepted"
            },
            {
              "decision_id": "dec_thermal_pid_accepted",
              "expected_state": "accepted",
              "gt_id": "PILOT_GT_TH_01",
              "gt_title": "Adopt Discrete PID Controller for Chamber Temperature Regulation",
              "overlap_count": 2,
              "shared_events": [
                "evt_adr_thermal_0004",
                "evt_git_thermal_a1b2c3d4"
              ],
              "system_state": "accepted"
            },
            {
              "decision_id": "dec_cache_local_lru_proposed",
              "expected_state": "rejected",
              "gt_id": "PILOT_GT_CACHE_02",
              "gt_title": "Retain In-Memory LRU Cache with Process Memory Cap",
              "overlap_count": 1,
              "shared_events": [
                "evt_pr_cache_38"
              ],
              "system_state": "superseded"
            }
          ],
          "lenient": {
            "correct_state_count": 2,
            "found": [
              {
                "decision_id": "dec_thermal_pid_accepted",
                "expected_state": "accepted",
                "gt_id": "PILOT_GT_TH_01",
                "gt_title": "Adopt Discrete PID Controller for Chamber Temperature Regulation",
                "system_state": "accepted"
              },
              {
                "decision_id": "dec_cache_redis_accepted",
                "expected_state": "accepted",
                "gt_id": "PILOT_GT_CACHE_01",
                "gt_title": "Migrate from In-Memory LRU to Distributed Redis Cluster",
                "system_state": "accepted"
              },
              {
                "decision_id": "dec_cache_local_lru_proposed",
                "expected_state": "rejected",
                "gt_id": "PILOT_GT_CACHE_02",
                "gt_title": "Retain In-Memory LRU Cache with Process Memory Cap",
                "system_state": "superseded"
              }
            ],
            "matched_gt_count": 3,
            "missed": [
              {
                "expected_evidence": [
                  "evt_issue_thermal_12_comm",
                  "evt_issue_thermal_12_sarah"
                ],
                "gt_id": "PILOT_GT_TH_02",
                "gt_title": "Reject Simple Deadband Hysteresis for Thermal Control"
              }
            ],
            "recall": 75.0,
            "state_accuracy": 66.7,
            "wrong_state": [
              {
                "decision_id": "dec_cache_local_lru_proposed",
                "expected_state": "rejected",
                "gt_id": "PILOT_GT_CACHE_02",
                "gt_title": "Retain In-Memory LRU Cache with Process Memory Cap",
                "system_state": "superseded"
              }
            ]
          },
          "missed": [
            {
              "expected_evidence": [
                "evt_issue_thermal_12_comm",
                "evt_issue_thermal_12_sarah"
              ],
              "gt_id": "PILOT_GT_TH_02",
              "gt_title": "Reject Simple Deadband Hysteresis for Thermal Control"
            }
          ],
          "overcounting_detected": false,
          "precision_reason": "snapshot hash mismatch: labels generated from 'def40ab257f7784709179e5f1e52d2815586c3f4e282fdb4e906e006f08ffeee', current DB hash is 'ec7e62cd3c0bba7fb9dd4f195355490a05e718a0389a0df8cf210b96aa3715ba'",
          "strict": {
            "correct_state_count": 2,
            "found": [
              {
                "decision_id": "dec_cache_redis_accepted",
                "expected_state": "accepted",
                "gt_id": "PILOT_GT_CACHE_01",
                "gt_title": "Migrate from In-Memory LRU to Distributed Redis Cluster",
                "overlap_count": 2,
                "shared_events": [
                  "evt_adr_cache_0009",
                  "evt_rev_cache_c201"
                ],
                "system_state": "accepted"
              },
              {
                "decision_id": "dec_thermal_pid_accepted",
                "expected_state": "accepted",
                "gt_id": "PILOT_GT_TH_01",
                "gt_title": "Adopt Discrete PID Controller for Chamber Temperature Regulation",
                "overlap_count": 2,
                "shared_events": [
                  "evt_adr_thermal_0004",
                  "evt_git_thermal_a1b2c3d4"
                ],
                "system_state": "accepted"
              },
              {
                "decision_id": "dec_cache_local_lru_proposed",
                "expected_state": "rejected",
                "gt_id": "PILOT_GT_CACHE_02",
                "gt_title": "Retain In-Memory LRU Cache with Process Memory Cap",
                "overlap_count": 1,
                "shared_events": [
                  "evt_pr_cache_38"
                ],
                "system_state": "superseded"
              }
            ],
            "matched_gt_count": 3,
            "matched_system_ids": [
              "dec_thermal_pid_accepted",
              "dec_cache_local_lru_proposed",
              "dec_cache_redis_accepted"
            ],
            "missed": [
              {
                "expected_evidence": [
                  "evt_issue_thermal_12_comm",
                  "evt_issue_thermal_12_sarah"
                ],
                "gt_id": "PILOT_GT_TH_02",
                "gt_title": "Reject Simple Deadband Hysteresis for Thermal Control"
              }
            ],
            "recall": 75.0,
            "state_accuracy": 66.7,
            "unmatched_system_count": 4,
            "unmatched_system_decisions": [
              {
                "alternatives_json": "[{\"description\": \"Deadband on-off threshold control +/- 1.5C\", \"rejection_reason\": \"Benchmarking revealed 17% higher latency and persistent 6.2C transient overshoot\", \"evidence_event_ids\": [\"evt_rev_thermal_comm2\"]}]",
                "confidence": 0.96,
                "decision_id": "dec_thermal_deadband_rejected",
                "evidence_assessment": "weak",
                "freshness": "fresh",
                "made_at": "2026-01-12T15:00:00Z",
                "made_by": "sarah_chen",
                "rationale": "Tested in simulation following Issue #12; deadband was insufficient to prevent emergency chamber thermal trip.",
                "repo": "acme-eng/thermal-control-system",
                "repo_full_name": "acme-eng/thermal-control-system",
                "review_status": "auto_confirmed",
                "state": "rejected",
                "superseded_by_decision_id": null,
                "supersedes_decision_id": null,
                "title": "Reject Simple Deadband Hysteresis for Thermal Control"
              },
              {
                "alternatives_json": "[]",
                "confidence": 0.8,
                "decision_id": "dec_thermal_pid_01",
                "evidence_assessment": "insufficient",
                "freshness": "fresh",
                "made_at": "2026-01-15T16:00:00Z",
                "made_by": "sarah_chen",
                "rationale": "Governing architectural baseline decision",
                "repo": "acme-eng/thermal-control-system",
                "repo_full_name": "acme-eng/thermal-control-system",
                "review_status": "pending_review",
                "state": "accepted",
                "superseded_by_decision_id": null,
                "supersedes_decision_id": null,
                "title": "Architectural Decision dec_thermal_pid_01"
              },
              {
                "alternatives_json": "[]",
                "confidence": 0.8,
                "decision_id": "dec_thermal_bangbang_02",
                "evidence_assessment": "insufficient",
                "freshness": "fresh",
                "made_at": "2026-01-12T15:00:00Z",
                "made_by": "sarah_chen",
                "rationale": "Governing architectural baseline decision",
                "repo": "acme-eng/thermal-control-system",
                "repo_full_name": "acme-eng/thermal-control-system",
                "review_status": "pending_review",
                "state": "rejected",
                "superseded_by_decision_id": null,
                "supersedes_decision_id": null,
                "title": "Architectural Decision dec_thermal_bangbang_02"
              },
              {
                "alternatives_json": "[]",
                "confidence": 0.8,
                "decision_id": "dec_cache_redis_01",
                "evidence_assessment": "insufficient",
                "freshness": "fresh",
                "made_at": "2026-02-06T15:00:00Z",
                "made_by": "priya_patel",
                "rationale": "Governing architectural baseline decision",
                "repo": "acme-eng/distributed-cache-service",
                "repo_full_name": "acme-eng/distributed-cache-service",
                "review_status": "pending_review",
                "state": "accepted",
                "superseded_by_decision_id": null,
                "supersedes_decision_id": null,
                "title": "Architectural Decision dec_cache_redis_01"
              }
            ],
            "unmatched_system_ids": [
              "dec_thermal_deadband_rejected",
              "dec_thermal_pid_01",
              "dec_thermal_bangbang_02",
              "dec_cache_redis_01"
            ],
            "wrong_state": [
              {
                "decision_id": "dec_cache_local_lru_proposed",
                "expected_state": "rejected",
                "gt_id": "PILOT_GT_CACHE_02",
                "gt_title": "Retain In-Memory LRU Cache with Process Memory Cap",
                "system_state": "superseded"
              }
            ]
          },
          "wrong_state": [
            {
              "decision_id": "dec_cache_local_lru_proposed",
              "expected_state": "rejected",
              "gt_id": "PILOT_GT_CACHE_02",
              "gt_title": "Retain In-Memory LRU Cache with Process Memory Cap",
              "system_state": "superseded"
            }
          ]
        },
        "drift_evaluation": {
          "fn": 0,
          "fp": 0,
          "precision": 100.0,
          "recall": 100.0,
          "status": "measured",
          "tn": 10,
          "total_cases": 20,
          "tp": 10
        },
        "finding_feedback": {
          "confirm": 0,
          "dismiss": 0,
          "reopen": 0,
          "total": 0
        },
        "ground_truth_total": 4,
        "matched_gt_count": 3,
        "matched_gt_count_lenient": 3,
        "matched_gt_count_strict": 3,
        "metrics": {
          "claim_support_rate": 0.0,
          "claim_supported": 0.0,
          "contradiction_precision": 100.0,
          "contradiction_recall": 100.0,
          "decision_extraction_f1": "not measured",
          "decision_extraction_precision": "not measured",
          "decision_extraction_recall": 75.0,
          "decision_recall_lenient": 75.0,
          "decision_recall_strict": 75.0,
          "drift_precision": 100.0,
          "drift_recall": 100.0,
          "event_exists": 100.0,
          "evidence_link_accuracy": 100.0,
          "finding_feedback_confirmed": 0,
          "finding_feedback_dismissed": 0,
          "finding_feedback_reopened": 0,
          "finding_feedback_total": 0,
          "processing_latency_ms": 15.0,
          "recall_difference": 0.0,
          "state_accuracy": 66.7,
          "state_accuracy_lenient": 66.7,
          "state_accuracy_strict": 66.7,
          "unsupported_claim_rate": 100.0,
          "url_format_ok": 100.0
        },
        "precision_reason": "snapshot hash mismatch: labels generated from 'def40ab257f7784709179e5f1e52d2815586c3f4e282fdb4e906e006f08ffeee', current DB hash is 'ec7e62cd3c0bba7fb9dd4f195355490a05e718a0389a0df8cf210b96aa3715ba'",
        "system_decisions_evaluated": 7,
        "unmatched_system_decisions_count": 4,
        "whybench_manifest": {
          "configurations": {
            "decision_threshold": 0.85,
            "extractor_mode": "heuristic",
            "llm_model": "none",
            "random_seed": 1234
          },
          "dataset_hashes": {
            "conflict_cases_sha256": "80f9337b9e01a7bad2c46402270c28151973610ef250cf7f867fe0d4aee2d548",
            "dataset_version": "whybench_v1",
            "db_snapshot_sha256": "26bd603a325232bd25e2e0fce3ef17daf916629f61bc25324b2afdd1ed8cc63d",
            "drift_cases_sha256": "1c9ee61e648ef1508faca6c00d7536ce0acb3447597cb91ab0cfb66998722f71",
            "precision_labels_sha256": "55e7a53f5c5af86e9948abaa80c7d8fc406ea8f6d49f6fb97411aa609e68fbce",
            "questions_sha256": "1e46e50dd8a35f6d6a7c33b7b5472521e982b4ff907cd91584a0bb962f9d94ab"
          },
          "environment": {
            "git_clean": true,
            "git_commit": "216b7cb08de014daaf7cf932af7f8fb8a1955855",
            "platform": "win32",
            "python_version": "3.11.6"
          },
          "manifest_version": "1.0",
          "metrics": {
            "overall": {
              "baseline_copilot": {
                "decision_recall": "not measured",
                "evaluated_samples": 0,
                "hallucination_rate": "not measured",
                "name": "Baseline D: GitHub Copilot",
                "status": "not measured"
              },
              "baseline_docs_only": {
                "decision_recall": 8.5,
                "found_count": 6,
                "name": "Baseline B: Documentation/ADRs Only",
                "note": "Task 1 (Evidence Retrieval) only; Task 2 (Decision Reconstruction) is n/a.",
                "status": "measured",
                "task_1_applicable": true,
                "task_1_hit_rate": 23.1,
                "task_1_top_k": 5,
                "task_2_applicable": false,
                "task_2_decision_recall": "n/a",
                "task_2_refusal_accuracy": "n/a (always answers)",
                "task_2_state_accuracy": "n/a",
                "top_k": 5,
                "total_count": 26,
                "wilson95_high": 0.4205,
                "wilson95_low": 0.1103
              },
              "baseline_keyword": {
                "decision_recall": 59.2,
                "found_count": 24,
                "name": "Baseline A: Keyword Search (Grep/BM25)",
                "note": "Task 1 (Evidence Retrieval) only; Task 2 (Decision Reconstruction) is n/a.",
                "status": "measured",
                "task_1_applicable": true,
                "task_1_hit_rate": 92.3,
                "task_1_top_k": 5,
                "task_2_applicable": false,
                "task_2_decision_recall": "n/a",
                "task_2_refusal_accuracy": "n/a (always answers)",
                "task_2_state_accuracy": "n/a",
                "top_k": 5,
                "total_count": 26,
                "wilson95_high": 0.9786,
                "wilson95_low": 0.7586
              },
              "baseline_llm": {
                "decision_recall": "not measured",
                "evidence_grounding_accuracy": "not measured",
                "name": "Baseline C: Plain LLM Q&A",
                "note": "Requires CIF_LLM_API_KEY and CIF_LLM_MODEL environment variables",
                "status": "not measured"
              },
              "calibration": {
                "assessment_accuracy": {},
                "calibrated": false,
                "ece": null,
                "ece_pct": null,
                "higher_scores_more_accurate": null,
                "labeled_count": 0,
                "min_required": 100,
                "monotonic_confidence": null,
                "reason": "not enough labels for calibration",
                "reliability_table": [],
                "status": "not measured"
              },
              "decision_precision": "not measured",
              "decision_precision_reason": "snapshot hash mismatch: labels generated from 'db0b1b05341cfddaab5a935aae3993ed12d5a355f86f014ba406e495bdf33d5a', current DB hash is '26bd603a325232bd25e2e0fce3ef17daf916629f61bc25324b2afdd1ed8cc63d'",
              "decision_recall_lenient": 80.8,
              "decision_recall_strict": 80.8,
              "lenient_matched_gt_count": 21,
              "recall_difference": 0.0,
              "refusal_accuracy": 64.4,
              "refusal_correct_count": 29,
              "state_accuracy": 100.0,
              "state_correct_count": 21,
              "strict_matched_gt_count": 21,
              "task_1_cif_hit_rate": 80.8,
              "task_1_cif_hits": 21,
              "task_1_cif_wilson95_high": 0.9149,
              "task_1_cif_wilson95_low": 0.6212
            },
            "per_repository": {
              "acme-ecommerce/payment-core": {
                "baseline_docs_only_hit_rate": 20.0,
                "baseline_docs_only_hits": 2,
                "baseline_docs_only_wilson95_high": 0.5098,
                "baseline_docs_only_wilson95_low": 0.0567,
                "baseline_keyword_hit_rate": 90.0,
                "baseline_keyword_hits": 9,
                "baseline_keyword_wilson95_high": 0.9821,
                "baseline_keyword_wilson95_low": 0.5958,
                "decision_precision": "not measured",
                "decision_precision_reason": "snapshot hash mismatch: labels generated from 'db0b1b05341cfddaab5a935aae3993ed12d5a355f86f014ba406e495bdf33d5a', current DB hash is '26bd603a325232bd25e2e0fce3ef17daf916629f61bc25324b2afdd1ed8cc63d'",
                "decision_recall_lenient": 80.0,
                "decision_recall_strict": 80.0,
                "lenient_matched_gt_count": 8,
                "questions_total": 25,
                "refusal_accuracy": 66.7,
                "refusal_correct_count": 10,
                "refusal_questions": 15,
                "standard_questions": 10,
                "state_accuracy": 100.0,
                "state_correct_count": 8,
                "strict_matched_gt_count": 8,
                "task_1_cif_hit_rate": 80.0,
                "task_1_cif_hits": 8,
                "task_1_cif_wilson95_high": 0.9433,
                "task_1_cif_wilson95_low": 0.4902
              },
              "cli/cli": {
                "baseline_docs_only_hit_rate": 25.0,
                "baseline_docs_only_hits": 2,
                "baseline_docs_only_wilson95_high": 0.5907,
                "baseline_docs_only_wilson95_low": 0.0715,
                "baseline_keyword_hit_rate": 100.0,
                "baseline_keyword_hits": 8,
                "baseline_keyword_wilson95_high": 1.0,
                "baseline_keyword_wilson95_low": 0.6756,
                "decision_precision": "not measured",
                "decision_precision_reason": "snapshot hash mismatch: labels generated from 'db0b1b05341cfddaab5a935aae3993ed12d5a355f86f014ba406e495bdf33d5a', current DB hash is '26bd603a325232bd25e2e0fce3ef17daf916629f61bc25324b2afdd1ed8cc63d'",
                "decision_recall_lenient": 87.5,
                "decision_recall_strict": 87.5,
                "lenient_matched_gt_count": 7,
                "questions_total": 23,
                "refusal_accuracy": 53.3,
                "refusal_correct_count": 8,
                "refusal_questions": 15,
                "standard_questions": 8,
                "state_accuracy": 100.0,
                "state_correct_count": 7,
                "strict_matched_gt_count": 7,
                "task_1_cif_hit_rate": 87.5,
                "task_1_cif_hits": 7,
                "task_1_cif_wilson95_high": 0.9776,
                "task_1_cif_wilson95_low": 0.5291
              },
              "cloud-hypervisor/cloud-hypervisor": {
                "baseline_docs_only_hit_rate": 25.0,
                "baseline_docs_only_hits": 2,
                "baseline_docs_only_wilson95_high": 0.5907,
                "baseline_docs_only_wilson95_low": 0.0715,
                "baseline_keyword_hit_rate": 87.5,
                "baseline_keyword_hits": 7,
                "baseline_keyword_wilson95_high": 0.9776,
                "baseline_keyword_wilson95_low": 0.5291,
                "decision_precision": "not measured",
                "decision_precision_reason": "snapshot hash mismatch: labels generated from 'db0b1b05341cfddaab5a935aae3993ed12d5a355f86f014ba406e495bdf33d5a', current DB hash is '26bd603a325232bd25e2e0fce3ef17daf916629f61bc25324b2afdd1ed8cc63d'",
                "decision_recall_lenient": 75.0,
                "decision_recall_strict": 75.0,
                "lenient_matched_gt_count": 6,
                "questions_total": 23,
                "refusal_accuracy": 73.3,
                "refusal_correct_count": 11,
                "refusal_questions": 15,
                "standard_questions": 8,
                "state_accuracy": 100.0,
                "state_correct_count": 6,
                "strict_matched_gt_count": 6,
                "task_1_cif_hit_rate": 75.0,
                "task_1_cif_hits": 6,
                "task_1_cif_wilson95_high": 0.9285,
                "task_1_cif_wilson95_low": 0.4093
              }
            }
          },
          "predictions": [
            {
              "expected_state": "accepted",
              "id": "WB_PAY_09",
              "is_refusal_case": false,
              "overlap_count": 2,
              "question": "How were double charges prevented when users double-clicked the checkout submit button?",
              "repo": "acme-ecommerce/payment-core",
              "state_match": true,
              "status": "found",
              "system_decision_id": "dec_acme-ecommerce_payment-core_github_pr_18",
              "system_state": "accepted"
            },
            {
              "expected_state": "rejected",
              "id": "WB_PAY_10",
              "is_refusal_case": false,
              "overlap_count": 1,
              "question": "Why were database row locks rejected for enforcing checkout idempotency?",
              "repo": "acme-ecommerce/payment-core",
              "state_match": true,
              "status": "found",
              "system_decision_id": "dec_acme-ecommerce_payment-core_pr_review_comment_c402",
              "system_state": "rejected"
            },
            {
              "expected_state": "accepted",
              "id": "WB_PAY_11",
              "is_refusal_case": false,
              "question": "How does payment-core authenticate incoming Stripe webhooks?",
              "repo": "acme-ecommerce/payment-core",
              "status": "missed"
            },
            {
              "expected_state": "rejected",
              "id": "WB_PAY_12",
              "is_refusal_case": false,
              "overlap_count": 1,
              "question": "Why was skipping webhook signature verification in development rejected?",
              "repo": "acme-ecommerce/payment-core",
              "state_match": true,
              "status": "found",
              "system_decision_id": "dec_acme-ecommerce_payment-core_pr_review_comment_c450",
              "system_state": "rejected"
            },
            {
              "expected_state": "accepted",
              "id": "WB_PAY_13",
              "is_refusal_case": false,
              "overlap_count": 1,
              "question": "How did payment-core implement support for customer partial refunds?",
              "repo": "acme-ecommerce/payment-core",
              "state_match": true,
              "status": "found",
              "system_decision_id": "dec_acme-ecommerce_payment-core_adr_docs_adr_0004-partial-refund-support_md",
              "system_state": "accepted"
            },
            {
              "expected_state": "accepted",
              "id": "WB_PAY_14",
              "is_refusal_case": false,
              "overlap_count": 2,
              "question": "How were fractional cent rounding errors solved in multi-currency refund calculations?",
              "repo": "acme-ecommerce/payment-core",
              "state_match": true,
              "status": "found",
              "system_decision_id": "dec_acme-ecommerce_payment-core_github_pr_29",
              "system_state": "accepted"
            },
            {
              "expected_state": "rejected",
              "id": "WB_PAY_15",
              "is_refusal_case": false,
              "overlap_count": 1,
              "question": "Why were client-supplied timestamps rejected for partial refund requests?",
              "repo": "acme-ecommerce/payment-core",
              "state_match": true,
              "status": "found",
              "system_decision_id": "dec_acme-ecommerce_payment-core_pr_review_comment_c505",
              "system_state": "rejected"
            },
            {
              "expected_state": "accepted",
              "id": "WB_PAY_16",
              "is_refusal_case": false,
              "question": "How does payment-core handle toxic malformed webhook messages that crash consumer workers?",
              "repo": "acme-ecommerce/payment-core",
              "status": "missed"
            },
            {
              "expected_state": "accepted",
              "id": "WB_PAY_17",
              "is_refusal_case": false,
              "overlap_count": 1,
              "question": "How does payment-core achieve PCI SAQ A compliance for credit card processing?",
              "repo": "acme-ecommerce/payment-core",
              "state_match": true,
              "status": "found",
              "system_decision_id": "dec_acme-ecommerce_payment-core_adr_docs_adr_0005-pci-token-vault_md",
              "system_state": "accepted"
            },
            {
              "expected_state": "rejected",
              "id": "WB_PAY_18",
              "is_refusal_case": false,
              "overlap_count": 1,
              "question": "Why was in-memory caching of card CVV security codes rejected?",
              "repo": "acme-ecommerce/payment-core",
              "state_match": true,
              "status": "found",
              "system_decision_id": "dec_acme-ecommerce_payment-core_pr_review_comment_c610",
              "system_state": "rejected"
            },
            {
              "expected_state": "rejected",
              "id": "WB_CH_09",
              "is_refusal_case": false,
              "overlap_count": 1,
              "question": "Why was legacy floppy and IDE drive emulation rejected?",
              "repo": "cloud-hypervisor/cloud-hypervisor",
              "state_match": true,
              "status": "found",
              "system_decision_id": "dec_cloud-hypervisor_cloud-hypervisor_pr_review_comment_c615",
              "system_state": "rejected"
            },
            {
              "expected_state": "accepted",
              "id": "WB_CH_10",
              "is_refusal_case": false,
              "overlap_count": 1,
              "question": "How does virtio-fs avoid memory duplication when sharing container root filesystems?",
              "repo": "cloud-hypervisor/cloud-hypervisor",
              "state_match": true,
              "status": "found",
              "system_decision_id": "dec_cloud-hypervisor_cloud-hypervisor_adr_docs_designs_virtio-fs_md",
              "system_state": "accepted"
            },
            {
              "expected_state": "accepted",
              "id": "WB_CH_11",
              "is_refusal_case": false,
              "overlap_count": 1,
              "question": "How does Cloud Hypervisor support dynamic hotplug of PCIe devices?",
              "repo": "cloud-hypervisor/cloud-hypervisor",
              "state_match": true,
              "status": "found",
              "system_decision_id": "dec_cloud-hypervisor_cloud-hypervisor_github_pr_1180",
              "system_state": "accepted"
            },
            {
              "expected_state": "accepted",
              "id": "WB_CH_12",
              "is_refusal_case": false,
              "overlap_count": 1,
              "question": "Why did Cloud Hypervisor adopt Linux io_uring for disk virtualization?",
              "repo": "cloud-hypervisor/cloud-hypervisor",
              "state_match": true,
              "status": "found",
              "system_decision_id": "dec_cloud-hypervisor_cloud-hypervisor_github_pr_1240",
              "system_state": "accepted"
            },
            {
              "expected_state": "rejected",
              "id": "WB_CH_13",
              "is_refusal_case": false,
              "overlap_count": 1,
              "question": "Why were spin-polling loops prohibited in io_uring worker threads?",
              "repo": "cloud-hypervisor/cloud-hypervisor",
              "state_match": true,
              "status": "found",
              "system_decision_id": "dec_cloud-hypervisor_cloud-hypervisor_pr_review_comment_c720",
              "system_state": "rejected"
            },
            {
              "expected_state": "accepted",
              "id": "WB_CH_14",
              "is_refusal_case": false,
              "question": "How does Cloud Hypervisor provide direct GPU access to guest virtual machines?",
              "repo": "cloud-hypervisor/cloud-hypervisor",
              "status": "missed"
            },
            {
              "expected_state": "accepted",
              "id": "WB_CH_15",
              "is_refusal_case": false,
              "overlap_count": 1,
              "question": "Why did Cloud Hypervisor adopt the ACPI Generic Event Device (GED)?",
              "repo": "cloud-hypervisor/cloud-hypervisor",
              "state_match": true,
              "status": "found",
              "system_decision_id": "dec_cloud-hypervisor_cloud-hypervisor_adr_docs_designs_acpi-ged_md",
              "system_state": "accepted"
            },
            {
              "expected_state": "accepted",
              "id": "WB_CH_16",
              "is_refusal_case": false,
              "question": "How does the microVM profile achieve 12ms cold boot for serverless sandboxes?",
              "repo": "cloud-hypervisor/cloud-hypervisor",
              "status": "missed"
            },
            {
              "expected_state": "rejected",
              "id": "WB_CLI_09",
              "is_refusal_case": false,
              "overlap_count": 1,
              "question": "Why was executing extensions via Go dynamic plugin packages rejected?",
              "repo": "cli/cli",
              "state_match": true,
              "status": "found",
              "system_decision_id": "dec_cli_cli_pr_review_comment_c712",
              "system_state": "rejected"
            },
            {
              "expected_state": "accepted",
              "id": "WB_CLI_10",
              "is_refusal_case": false,
              "overlap_count": 2,
              "question": "How does GitHub CLI isolate extension subprocess execution environment?",
              "repo": "cli/cli",
              "state_match": true,
              "status": "found",
              "system_decision_id": "dec_cli_cli_github_pr_670",
              "system_state": "accepted"
            },
            {
              "expected_state": "accepted",
              "id": "WB_CLI_11",
              "is_refusal_case": false,
              "overlap_count": 1,
              "question": "Why did GitHub CLI adopt termenv for terminal formatting?",
              "repo": "cli/cli",
              "state_match": true,
              "status": "found",
              "system_decision_id": "dec_cli_cli_adr_docs_rfc_004-termenv-formatting_md",
              "system_state": "accepted"
            },
            {
              "expected_state": "accepted",
              "id": "WB_CLI_12",
              "is_refusal_case": false,
              "overlap_count": 2,
              "question": "How was ANSI escape sequence corruption resolved in Unix pipelines?",
              "repo": "cli/cli",
              "state_match": true,
              "status": "found",
              "system_decision_id": "dec_cli_cli_github_pr_735",
              "system_state": "accepted"
            },
            {
              "expected_state": "accepted",
              "id": "WB_CLI_13",
              "is_refusal_case": false,
              "overlap_count": 1,
              "question": "How does GitHub CLI share credentials with standard Git CLI operations?",
              "repo": "cli/cli",
              "state_match": true,
              "status": "found",
              "system_decision_id": "dec_cli_cli_adr_docs_rfc_005-git-credential-helper_md",
              "system_state": "accepted"
            },
            {
              "expected_state": "accepted",
              "id": "WB_CLI_14",
              "is_refusal_case": false,
              "overlap_count": 1,
              "question": "How is git credential helper configured during authentication?",
              "repo": "cli/cli",
              "state_match": true,
              "status": "found",
              "system_decision_id": "dec_cli_cli_github_pr_810",
              "system_state": "accepted"
            },
            {
              "expected_state": "rejected",
              "id": "WB_CLI_15",
              "is_refusal_case": false,
              "overlap_count": 1,
              "question": "Why was passing authentication tokens via URL query parameters rejected?",
              "repo": "cli/cli",
              "state_match": true,
              "status": "found",
              "system_decision_id": "dec_cli_cli_pr_review_comment_c840",
              "system_state": "rejected"
            },
            {
              "expected_state": "accepted",
              "id": "WB_CLI_16",
              "is_refusal_case": false,
              "question": "How does gh auth login authenticate in headless SSH cloud environments without a browser?",
              "repo": "cli/cli",
              "status": "missed"
            },
            {
              "expected_state": "none",
              "id": "WB_PAY_TEST_NEG_01",
              "is_refusal_case": true,
              "negative_type": "unrecorded",
              "question": "Why did payment-core switch from JSON REST APIs to XML SOAP for payment endpoints?",
              "repo": "acme-ecommerce/payment-core",
              "status": "correct_refusal",
              "system_answer": "No recorded architectural decision found (Refused)"
            },
            {
              "expected_state": "none",
              "id": "WB_PAY_TEST_NEG_02",
              "is_refusal_case": true,
              "negative_type": "unrecorded",
              "question": "Why does payment-core store customer passwords in base64 plaintext in database tables?",
              "repo": "acme-ecommerce/payment-core",
              "status": "correct_refusal",
              "system_answer": "No recorded architectural decision found (Refused)"
            },
            {
              "expected_state": "none",
              "id": "WB_PAY_TEST_NEG_03",
              "is_refusal_case": true,
              "negative_type": "unrecorded",
              "question": "Why was Apache Cassandra chosen over PostgreSQL for payment database persistence?",
              "repo": "acme-ecommerce/payment-core",
              "status": "correct_refusal",
              "system_answer": "No recorded architectural decision found (Refused)"
            },
            {
              "expected_state": "none",
              "id": "WB_PAY_TEST_NEG_04",
              "is_refusal_case": true,
              "negative_type": "unrecorded",
              "question": "Why did payment-core mandate SOAP envelope encoding for Stripe charge requests?",
              "repo": "acme-ecommerce/payment-core",
              "status": "correct_refusal",
              "system_answer": "No recorded architectural decision found (Refused)"
            },
            {
              "expected_state": "none",
              "id": "WB_PAY_TEST_NEG_05",
              "is_refusal_case": true,
              "negative_type": "unrecorded",
              "question": "Why was Elasticsearch adopted as the primary ACID transactional ledger for checkout balances?",
              "repo": "acme-ecommerce/payment-core",
              "status": "correct_refusal",
              "system_answer": "No recorded architectural decision found (Refused)"
            },
            {
              "expected_state": "none",
              "id": "WB_PAY_TEST_NEG_06",
              "is_refusal_case": true,
              "negative_type": "unrecorded",
              "question": "Why did payment-core replace JWT token authentication with Basic HTTP auth over unencrypted ports?",
              "repo": "acme-ecommerce/payment-core",
              "status": "correct_refusal",
              "system_answer": "No recorded architectural decision found (Refused)"
            },
            {
              "expected_state": "none",
              "id": "WB_PAY_TEST_NEG_07",
              "is_refusal_case": true,
              "negative_type": "unrecorded",
              "question": "Why was CouchDB adopted for storing customer multi-currency wallet balances?",
              "repo": "acme-ecommerce/payment-core",
              "status": "correct_refusal",
              "system_answer": "No recorded architectural decision found (Refused)"
            },
            {
              "expected_state": "none",
              "id": "WB_PAY_TEST_NEG_08",
              "is_refusal_case": true,
              "negative_type": "mention_without_decision",
              "question": "Did PR #18 review comments decide to adopt Memcached alongside Redis for idempotency?",
              "repo": "acme-ecommerce/payment-core",
              "status": "false_positive_decision",
              "system_decision_id": "dec_acme-ecommerce_payment-core_github_pr_18"
            },
            {
              "expected_state": "none",
              "id": "WB_PAY_TEST_NEG_09",
              "is_refusal_case": true,
              "negative_type": "mention_without_decision",
              "question": "Was Apache Pulsar evaluated and chosen for webhook message ingestion in issue #19?",
              "repo": "acme-ecommerce/payment-core",
              "status": "correct_refusal",
              "system_answer": "No recorded architectural decision found (Refused)"
            },
            {
              "expected_state": "none",
              "id": "WB_PAY_TEST_NEG_10",
              "is_refusal_case": true,
              "negative_type": "mention_without_decision",
              "question": "Did issue #8 contributor comments decide to replace Python threading with asyncio event loop across all services?",
              "repo": "acme-ecommerce/payment-core",
              "status": "false_positive_decision",
              "system_decision_id": "dec_acme-ecommerce_payment-core_github_pr_14"
            },
            {
              "expected_state": "none",
              "id": "WB_PAY_TEST_NEG_11",
              "is_refusal_case": true,
              "negative_type": "mention_without_decision",
              "question": "Did PR #22 discussion adopt OpenTelemetry SDK for tracing webhook signature verification latency?",
              "repo": "acme-ecommerce/payment-core",
              "status": "correct_refusal",
              "system_answer": "No recorded architectural decision found (Refused)"
            },
            {
              "expected_state": "none",
              "id": "WB_PAY_TEST_NEG_12",
              "is_refusal_case": true,
              "negative_type": "mention_without_decision",
              "question": "Was JSON Web Encryption (JWE) chosen to wrap webhook payloads in PR #35 discussions?",
              "repo": "acme-ecommerce/payment-core",
              "status": "correct_refusal",
              "system_answer": "No recorded architectural decision found (Refused)"
            },
            {
              "expected_state": "none",
              "id": "WB_PAY_TEST_NEG_13",
              "is_refusal_case": true,
              "negative_type": "mention_without_decision",
              "question": "Did release notes mentioning Stripe SDK v10 in PR #14 adopt automatic Stripe telemetry sharing?",
              "repo": "acme-ecommerce/payment-core",
              "status": "false_positive_decision",
              "system_decision_id": "dec_acme-ecommerce_payment-core_github_pr_14"
            },
            {
              "expected_state": "none",
              "id": "WB_PAY_TEST_NEG_14",
              "is_refusal_case": true,
              "negative_type": "mention_without_decision",
              "question": "Was AWS KMS adopted for credit card token encryption in PR #38 review discussion?",
              "repo": "acme-ecommerce/payment-core",
              "status": "false_positive_decision",
              "system_decision_id": "dec_acme-ecommerce_payment-core_pr_review_comment_c610"
            },
            {
              "expected_state": "none",
              "id": "WB_PAY_TEST_NEG_15",
              "is_refusal_case": true,
              "negative_type": "mention_without_decision",
              "question": "Did dependabot dependency upgrade comments on PR #29 decide to replace Decimal with GMP big-integer library?",
              "repo": "acme-ecommerce/payment-core",
              "status": "false_positive_decision",
              "system_decision_id": "dec_acme-ecommerce_payment-core_github_pr_29"
            },
            {
              "expected_state": "none",
              "id": "WB_CH_TEST_NEG_01",
              "is_refusal_case": true,
              "negative_type": "unrecorded",
              "question": "Why did Cloud Hypervisor embed a proprietary binary NVIDIA kernel driver into the VMM?",
              "repo": "cloud-hypervisor/cloud-hypervisor",
              "status": "correct_refusal",
              "system_answer": "No recorded architectural decision found (Refused)"
            },
            {
              "expected_state": "none",
              "id": "WB_CH_TEST_NEG_02",
              "is_refusal_case": true,
              "negative_type": "unrecorded",
              "question": "Why does Cloud Hypervisor bundle an unencrypted FTP server inside the guest VM tree?",
              "repo": "cloud-hypervisor/cloud-hypervisor",
              "status": "correct_refusal",
              "system_answer": "No recorded architectural decision found (Refused)"
            },
            {
              "expected_state": "none",
              "id": "WB_CH_TEST_NEG_03",
              "is_refusal_case": true,
              "negative_type": "unrecorded",
              "question": "Why did Cloud Hypervisor replace KVM with an interpreted bytecode software CPU emulator?",
              "repo": "cloud-hypervisor/cloud-hypervisor",
              "status": "correct_refusal",
              "system_answer": "No recorded architectural decision found (Refused)"
            },
            {
              "expected_state": "none",
              "id": "WB_CH_TEST_NEG_04",
              "is_refusal_case": true,
              "negative_type": "unrecorded",
              "question": "Why did Cloud Hypervisor mandate MS-DOS 6.22 compatibility mode for cloud serverless profiles?",
              "repo": "cloud-hypervisor/cloud-hypervisor",
              "status": "correct_refusal",
              "system_answer": "No recorded architectural decision found (Refused)"
            },
            {
              "expected_state": "none",
              "id": "WB_CH_TEST_NEG_05",
              "is_refusal_case": true,
              "negative_type": "unrecorded",
              "question": "Why was VirtualBox VDI disk format adopted over raw sparse files in Cloud Hypervisor?",
              "repo": "cloud-hypervisor/cloud-hypervisor",
              "status": "correct_refusal",
              "system_answer": "No recorded architectural decision found (Refused)"
            },
            {
              "expected_state": "none",
              "id": "WB_CH_TEST_NEG_06",
              "is_refusal_case": true,
              "negative_type": "unrecorded",
              "question": "Why did Cloud Hypervisor replace Rust-VMM crates with Java JNI virtualization bindings?",
              "repo": "cloud-hypervisor/cloud-hypervisor",
              "status": "correct_refusal",
              "system_answer": "No recorded architectural decision found (Refused)"
            },
            {
              "expected_state": "none",
              "id": "WB_CH_TEST_NEG_07",
              "is_refusal_case": true,
              "negative_type": "unrecorded",
              "question": "Why was Telnet protocol chosen for VM hypervisor management socket?",
              "repo": "cloud-hypervisor/cloud-hypervisor",
              "status": "correct_refusal",
              "system_answer": "No recorded architectural decision found (Refused)"
            },
            {
              "expected_state": "none",
              "id": "WB_CH_TEST_NEG_08",
              "is_refusal_case": true,
              "negative_type": "mention_without_decision",
              "question": "Did issue #890 discussions decide to adopt ZFS pool storage for guest memory swapping?",
              "repo": "cloud-hypervisor/cloud-hypervisor",
              "status": "correct_refusal",
              "system_answer": "No recorded architectural decision found (Refused)"
            },
            {
              "expected_state": "none",
              "id": "WB_CH_TEST_NEG_09",
              "is_refusal_case": true,
              "negative_type": "mention_without_decision",
              "question": "Was Tokio async runtime chosen over standard threads in PR #1240 io_uring discussions?",
              "repo": "cloud-hypervisor/cloud-hypervisor",
              "status": "false_positive_decision",
              "system_decision_id": "dec_cloud-hypervisor_cloud-hypervisor_github_pr_1240"
            },
            {
              "expected_state": "none",
              "id": "WB_CH_TEST_NEG_10",
              "is_refusal_case": true,
              "negative_type": "mention_without_decision",
              "question": "Did PR #1312 discuss and adopt NVIDIA proprietary vGPU grid licensing manager?",
              "repo": "cloud-hypervisor/cloud-hypervisor",
              "status": "correct_refusal",
              "system_answer": "No recorded architectural decision found (Refused)"
            },
            {
              "expected_state": "none",
              "id": "WB_CH_TEST_NEG_11",
              "is_refusal_case": true,
              "negative_type": "mention_without_decision",
              "question": "Did issue #940 discuss adopting Intel CAT (Cache Allocation Technology) for vCPU cache isolation?",
              "repo": "cloud-hypervisor/cloud-hypervisor",
              "status": "false_positive_decision",
              "system_decision_id": "dec_cloud-hypervisor_cloud-hypervisor_github_issue_940"
            },
            {
              "expected_state": "none",
              "id": "WB_CH_TEST_NEG_12",
              "is_refusal_case": true,
              "negative_type": "mention_without_decision",
              "question": "Was GlusterFS evaluated for virtio-fs multi-node cluster backend in issue #1015?",
              "repo": "cloud-hypervisor/cloud-hypervisor",
              "status": "correct_refusal",
              "system_answer": "No recorded architectural decision found (Refused)"
            },
            {
              "expected_state": "none",
              "id": "WB_CH_TEST_NEG_13",
              "is_refusal_case": true,
              "negative_type": "mention_without_decision",
              "question": "Did PR #1180 comments adopt Thunderbolt PCIe external hotplug device specifications?",
              "repo": "cloud-hypervisor/cloud-hypervisor",
              "status": "false_positive_decision",
              "system_decision_id": "dec_cloud-hypervisor_cloud-hypervisor_github_pr_1180"
            },
            {
              "expected_state": "none",
              "id": "WB_CH_TEST_NEG_14",
              "is_refusal_case": true,
              "negative_type": "mention_without_decision",
              "question": "Did bot automated benchmark comments on PR #1042 decide to enforce 1GB hugepages for all guests?",
              "repo": "cloud-hypervisor/cloud-hypervisor",
              "status": "false_positive_decision",
              "system_decision_id": "dec_cloud-hypervisor_cloud-hypervisor_github_pr_1042"
            },
            {
              "expected_state": "none",
              "id": "WB_CH_TEST_NEG_15",
              "is_refusal_case": true,
              "negative_type": "mention_without_decision",
              "question": "Was gVisor container sandbox architecture adopted in PR #1390 serverless profile?",
              "repo": "cloud-hypervisor/cloud-hypervisor",
              "status": "correct_refusal",
              "system_answer": "No recorded architectural decision found (Refused)"
            },
            {
              "expected_state": "none",
              "id": "WB_CLI_TEST_NEG_01",
              "is_refusal_case": true,
              "negative_type": "unrecorded",
              "question": "Why did GitHub CLI migrate all commands to PHP scripts?",
              "repo": "cli/cli",
              "status": "correct_refusal",
              "system_answer": "No recorded architectural decision found (Refused)"
            },
            {
              "expected_state": "none",
              "id": "WB_CLI_TEST_NEG_02",
              "is_refusal_case": true,
              "negative_type": "unrecorded",
              "question": "Why does GitHub CLI store OAuth secrets in unencrypted web cookies?",
              "repo": "cli/cli",
              "status": "correct_refusal",
              "system_answer": "No recorded architectural decision found (Refused)"
            },
            {
              "expected_state": "none",
              "id": "WB_CLI_TEST_NEG_03",
              "is_refusal_case": true,
              "negative_type": "unrecorded",
              "question": "Why did GitHub CLI disable TLS verification for enterprise GitHub instances by default?",
              "repo": "cli/cli",
              "status": "correct_refusal",
              "system_answer": "No recorded architectural decision found (Refused)"
            },
            {
              "expected_state": "none",
              "id": "WB_CLI_TEST_NEG_04",
              "is_refusal_case": true,
              "negative_type": "unrecorded",
              "question": "Why was the gh CLI command line interface rewritten in Perl?",
              "repo": "cli/cli",
              "status": "correct_refusal",
              "system_answer": "No recorded architectural decision found (Refused)"
            },
            {
              "expected_state": "none",
              "id": "WB_CLI_TEST_NEG_05",
              "is_refusal_case": true,
              "negative_type": "unrecorded",
              "question": "Why did GitHub CLI mandate Google Chrome installation for running gh auth login?",
              "repo": "cli/cli",
              "status": "correct_refusal",
              "system_answer": "No recorded architectural decision found (Refused)"
            },
            {
              "expected_state": "none",
              "id": "WB_CLI_TEST_NEG_06",
              "is_refusal_case": true,
              "negative_type": "unrecorded",
              "question": "Why was Apache Thrift adopted as the RPC layer for GitHub CLI commands?",
              "repo": "cli/cli",
              "status": "correct_refusal",
              "system_answer": "No recorded architectural decision found (Refused)"
            },
            {
              "expected_state": "none",
              "id": "WB_CLI_TEST_NEG_07",
              "is_refusal_case": true,
              "negative_type": "unrecorded",
              "question": "Why did GitHub CLI deprecate git command line wrapper execution in favor of libgit2 C library?",
              "repo": "cli/cli",
              "status": "correct_refusal",
              "system_answer": "No recorded architectural decision found (Refused)"
            },
            {
              "expected_state": "none",
              "id": "WB_CLI_TEST_NEG_08",
              "is_refusal_case": true,
              "negative_type": "mention_without_decision",
              "question": "Did issue #412 discussions decide to adopt GnuPG pass password manager for token persistence?",
              "repo": "cli/cli",
              "status": "false_positive_decision",
              "system_decision_id": "dec_cli_cli_github_pr_518"
            },
            {
              "expected_state": "none",
              "id": "WB_CLI_TEST_NEG_09",
              "is_refusal_case": true,
              "negative_type": "mention_without_decision",
              "question": "Was AWS Secrets Manager integration adopted in PR #518 comments for cloud tokens?",
              "repo": "cli/cli",
              "status": "false_positive_decision",
              "system_decision_id": "dec_cli_cli_github_pr_518"
            },
            {
              "expected_state": "none",
              "id": "WB_CLI_TEST_NEG_10",
              "is_refusal_case": true,
              "negative_type": "mention_without_decision",
              "question": "Did PR #670 decide to use Firejail sandboxing for third-party extensions?",
              "repo": "cli/cli",
              "status": "false_positive_decision",
              "system_decision_id": "dec_cli_cli_github_pr_670"
            },
            {
              "expected_state": "none",
              "id": "WB_CLI_TEST_NEG_11",
              "is_refusal_case": true,
              "negative_type": "mention_without_decision",
              "question": "Did issue #480 discuss switching to gRPC-Web for repository pull request pagination?",
              "repo": "cli/cli",
              "status": "false_positive_decision",
              "system_decision_id": "dec_cli_cli_github_pr_592"
            },
            {
              "expected_state": "none",
              "id": "WB_CLI_TEST_NEG_12",
              "is_refusal_case": true,
              "negative_type": "mention_without_decision",
              "question": "Was Bubble Tea TUI framework adopted for rendering terminal output in PR #735?",
              "repo": "cli/cli",
              "status": "false_positive_decision",
              "system_decision_id": "dec_cli_cli_github_pr_735"
            },
            {
              "expected_state": "none",
              "id": "WB_CLI_TEST_NEG_13",
              "is_refusal_case": true,
              "negative_type": "mention_without_decision",
              "question": "Did PR #810 review discussion decide to support Kerberos SPNEGO authentication?",
              "repo": "cli/cli",
              "status": "false_positive_decision",
              "system_decision_id": "dec_cli_cli_github_pr_810"
            },
            {
              "expected_state": "none",
              "id": "WB_CLI_TEST_NEG_14",
              "is_refusal_case": true,
              "negative_type": "mention_without_decision",
              "question": "Did issue #780 adopt an embedded micro-webserver for OAuth redirect handling on headless servers?",
              "repo": "cli/cli",
              "status": "correct_refusal",
              "system_answer": "No recorded architectural decision found (Refused)"
            },
            {
              "expected_state": "none",
              "id": "WB_CLI_TEST_NEG_15",
              "is_refusal_case": true,
              "negative_type": "mention_without_decision",
              "question": "Did dependabot comments on PR #592 decide to replace shurcooL/graphql with khan/genqlient?",
              "repo": "cli/cli",
              "status": "false_positive_decision",
              "system_decision_id": "dec_cli_cli_github_pr_592"
            }
          ],
          "questions_evaluated": 71,
          "refusal_questions": 45,
          "run_id": "test_v2_20261013_100423",
          "split": "test_v2",
          "standard_questions": 26,
          "task1_fair_corrections": {
            "cif_metric_definition": "single strictly-matched decision cites >=1 expected evidence event; not a ranked top-5 retrieval",
            "generated_by": "tools/recompute_task1_fair.py",
            "original_values": {
              "baseline_docs_only_rate": 8.5,
              "baseline_docs_only_total_count": 71,
              "baseline_keyword_rate": 59.2,
              "baseline_keyword_total_count": 71
            },
            "overall": {
              "baseline_docs_only": {
                "hits": 6,
                "n": 26,
                "rate": 23.1,
                "wilson95_high": 0.4205,
                "wilson95_low": 0.1103
              },
              "baseline_keyword": {
                "hits": 24,
                "n": 26,
                "rate": 92.3,
                "wilson95_high": 0.9786,
                "wilson95_low": 0.7586
              },
              "cif": {
                "hits": 21,
                "n": 26,
                "rate": 80.8,
                "wilson95_high": 0.9149,
                "wilson95_low": 0.6212
              }
            },
            "per_repository": {
              "acme-ecommerce/payment-core": {
                "baseline_docs_only": {
                  "hits": 2,
                  "n": 10,
                  "original_rate": 8.0,
                  "rate": 20.0,
                  "wilson95_high": 0.5098,
                  "wilson95_low": 0.0567
                },
                "baseline_keyword": {
                  "hits": 9,
                  "n": 10,
                  "original_rate": 56.0,
                  "rate": 90.0,
                  "wilson95_high": 0.9821,
                  "wilson95_low": 0.5958
                },
                "cif": {
                  "hits": 8,
                  "n": 10,
                  "rate": 80.0,
                  "wilson95_high": 0.9433,
                  "wilson95_low": 0.4902
                },
                "positives_n": 10
              },
              "cli/cli": {
                "baseline_docs_only": {
                  "hits": 2,
                  "n": 8,
                  "original_rate": 8.7,
                  "rate": 25.0,
                  "wilson95_high": 0.5907,
                  "wilson95_low": 0.0715
                },
                "baseline_keyword": {
                  "hits": 8,
                  "n": 8,
                  "original_rate": 56.5,
                  "rate": 100.0,
                  "wilson95_high": 1.0,
                  "wilson95_low": 0.6756
                },
                "cif": {
                  "hits": 7,
                  "n": 8,
                  "rate": 87.5,
                  "wilson95_high": 0.9776,
                  "wilson95_low": 0.5291
                },
                "positives_n": 8
              },
              "cloud-hypervisor/cloud-hypervisor": {
                "baseline_docs_only": {
                  "hits": 2,
                  "n": 8,
                  "original_rate": 8.7,
                  "rate": 25.0,
                  "wilson95_high": 0.5907,
                  "wilson95_low": 0.0715
                },
                "baseline_keyword": {
                  "hits": 7,
                  "n": 8,
                  "original_rate": 65.2,
                  "rate": 87.5,
                  "wilson95_high": 0.9776,
                  "wilson95_low": 0.5291
                },
                "cif": {
                  "hits": 6,
                  "n": 8,
                  "rate": 75.0,
                  "wilson95_high": 0.9285,
                  "wilson95_low": 0.4093
                },
                "positives_n": 8
              }
            },
            "positives_n": 26,
            "reason": "baselines were originally scored over all questions incl. negatives; CIF over positives only",
            "split": "test_v2"
          },
          "timestamp": "2026-10-13T10:04:34.739827"
        }
      },
      "status": "success"
    },
    "bus_factor": {
      "modules": [
        {
          "bus_factor": 1,
          "contributors": [
            {
              "contributor": "sarah_chen",
              "knowledge_score": 5.5,
              "share": 1.0
            }
          ],
          "documentation_coverage": 1.0,
          "important_decisions_count": 1,
          "module": "core",
          "onboarding_hint": "Concentration risk: sarah_chen holds 100% of module knowledge.",
          "risk_level": "high",
          "single_contributor_decisions": 1,
          "single_contributor_share": 1.0,
          "top_contributor": "sarah_chen",
          "top_contributor_share": 1.0
        },
        {
          "bus_factor": 1,
          "contributors": [
            {
              "contributor": "sarah_chen",
              "knowledge_score": 10.5,
              "share": 0.84
            },
            {
              "contributor": "marcus_vance",
              "knowledge_score": 2.0,
              "share": 0.16
            }
          ],
          "documentation_coverage": 0.5,
          "important_decisions_count": 2,
          "module": "thermal",
          "onboarding_hint": "Concentration risk: sarah_chen holds 84% of module knowledge.",
          "risk_level": "high",
          "single_contributor_decisions": 1,
          "single_contributor_share": 0.5,
          "top_contributor": "sarah_chen",
          "top_contributor_share": 0.84
        }
      ],
      "overall_bus_factor": 1,
      "repo": "acme-eng/thermal-control-system",
      "status": "success",
      "total_modules": 2
    },
    "bus_factor_cache": {
      "modules": [
        {
          "bus_factor": 1,
          "contributors": [
            {
              "contributor": "priya_patel",
              "knowledge_score": 7.5,
              "share": 1.0
            }
          ],
          "documentation_coverage": 1.0,
          "important_decisions_count": 1,
          "module": "core",
          "onboarding_hint": "Concentration risk: priya_patel holds 100% of module knowledge.",
          "risk_level": "high",
          "single_contributor_decisions": 1,
          "single_contributor_share": 1.0,
          "top_contributor": "priya_patel",
          "top_contributor_share": 1.0
        },
        {
          "bus_factor": 1,
          "contributors": [
            {
              "contributor": "priya_patel",
              "knowledge_score": 7.5,
              "share": 0.625
            },
            {
              "contributor": "marcus_vance",
              "knowledge_score": 4.5,
              "share": 0.375
            }
          ],
          "documentation_coverage": 0.5,
          "important_decisions_count": 2,
          "module": "cache",
          "onboarding_hint": "Concentration risk: priya_patel holds 62% of module knowledge.",
          "risk_level": "high",
          "single_contributor_decisions": 2,
          "single_contributor_share": 1.0,
          "top_contributor": "priya_patel",
          "top_contributor_share": 0.625
        }
      ],
      "overall_bus_factor": 1,
      "repo": "acme-eng/distributed-cache-service",
      "status": "success",
      "total_modules": 2
    },
    "bus_factor_thermal": {
      "modules": [
        {
          "bus_factor": 1,
          "contributors": [
            {
              "contributor": "sarah_chen",
              "knowledge_score": 5.5,
              "share": 1.0
            }
          ],
          "documentation_coverage": 1.0,
          "important_decisions_count": 1,
          "module": "core",
          "onboarding_hint": "Concentration risk: sarah_chen holds 100% of module knowledge.",
          "risk_level": "high",
          "single_contributor_decisions": 1,
          "single_contributor_share": 1.0,
          "top_contributor": "sarah_chen",
          "top_contributor_share": 1.0
        },
        {
          "bus_factor": 1,
          "contributors": [
            {
              "contributor": "sarah_chen",
              "knowledge_score": 10.5,
              "share": 0.84
            },
            {
              "contributor": "marcus_vance",
              "knowledge_score": 2.0,
              "share": 0.16
            }
          ],
          "documentation_coverage": 0.5,
          "important_decisions_count": 2,
          "module": "thermal",
          "onboarding_hint": "Concentration risk: sarah_chen holds 84% of module knowledge.",
          "risk_level": "high",
          "single_contributor_decisions": 1,
          "single_contributor_share": 0.5,
          "top_contributor": "sarah_chen",
          "top_contributor_share": 0.84
        }
      ],
      "overall_bus_factor": 1,
      "repo": "acme-eng/thermal-control-system",
      "status": "success",
      "total_modules": 2
    },
    "decisions_all": {
      "data": [
        {
          "alternatives_considered": [
            {
              "description": "In-memory LRU cache with soft memory cap (PR #38)",
              "evidence_event_ids": [
                "evt_rev_cache_c201"
              ],
              "rejection_reason": "Rejected: Local cache causes cache stampedes and memory duplication across container replicas"
            }
          ],
          "alternatives_json": "[{\"description\": \"In-memory LRU cache with soft memory cap (PR #38)\", \"rejection_reason\": \"Rejected: Local cache causes cache stampedes and memory duplication across container replicas\", \"evidence_event_ids\": [\"evt_rev_cache_c201\"]}]",
          "confidence": 0.97,
          "decision_id": "dec_cache_redis_accepted",
          "evidence_assessment": "insufficient",
          "evidence_count": 2,
          "freshness": "fresh",
          "made_at": "2026-02-06T15:00:00Z",
          "made_by": "priya_patel",
          "rationale": "ADR 0009: Decommission local in-memory dict and migrate to Redis cluster to prevent container OOMs and maintain cache consistency across autoscaled pods.",
          "repo": "acme-eng/distributed-cache-service",
          "repo_full_name": "acme-eng/distributed-cache-service",
          "review_status": "auto_confirmed",
          "state": "accepted",
          "superseded_by_decision_id": null,
          "supersedes_decision_id": "dec_cache_local_lru_proposed",
          "title": "Migrate from In-Memory LRU to Distributed Redis Cluster"
        },
        {
          "alternatives_considered": [],
          "alternatives_json": "[]",
          "confidence": 0.8,
          "decision_id": "dec_cache_redis_01",
          "evidence_assessment": "insufficient",
          "evidence_count": 1,
          "freshness": "fresh",
          "made_at": "2026-02-06T15:00:00Z",
          "made_by": "priya_patel",
          "rationale": "Governing architectural baseline decision",
          "repo": "acme-eng/distributed-cache-service",
          "repo_full_name": "acme-eng/distributed-cache-service",
          "review_status": "pending_review",
          "state": "accepted",
          "superseded_by_decision_id": null,
          "supersedes_decision_id": null,
          "title": "Architectural Decision dec_cache_redis_01"
        },
        {
          "alternatives_considered": [
            {
              "description": "Redis cluster deployment",
              "evidence_event_ids": [
                "evt_pr_cache_38"
              ],
              "rejection_reason": "Adds operational complexity and 1-2ms network hop over in-process memory"
            }
          ],
          "alternatives_json": "[{\"description\": \"Redis cluster deployment\", \"rejection_reason\": \"Adds operational complexity and 1-2ms network hop over in-process memory\", \"evidence_event_ids\": [\"evt_pr_cache_38\"]}]",
          "confidence": 0.82,
          "decision_id": "dec_cache_local_lru_proposed",
          "evidence_assessment": "weak",
          "evidence_count": 1,
          "freshness": "fresh",
          "made_at": "2026-02-03T14:30:00Z",
          "made_by": "marcus_vance",
          "rationale": "Keep cache strictly inside Python heap to guarantee sub-millisecond access and avoid external Redis infra.",
          "repo": "acme-eng/distributed-cache-service",
          "repo_full_name": "acme-eng/distributed-cache-service",
          "review_status": "pending_review",
          "state": "superseded",
          "superseded_by_decision_id": "dec_cache_redis_accepted",
          "supersedes_decision_id": null,
          "title": "Retain In-Memory LRU Cache with Process Memory Cap"
        },
        {
          "alternatives_considered": [
            {
              "description": "On-off hysteresis deadband controller",
              "evidence_event_ids": [
                "evt_rev_thermal_comm2"
              ],
              "rejection_reason": "Caused 17% latency increase and 6.2C overshoot in thermal transient tests"
            }
          ],
          "alternatives_json": "[{\"description\": \"On-off hysteresis deadband controller\", \"rejection_reason\": \"Caused 17% latency increase and 6.2C overshoot in thermal transient tests\", \"evidence_event_ids\": [\"evt_rev_thermal_comm2\"]}]",
          "confidence": 0.98,
          "decision_id": "dec_thermal_pid_accepted",
          "evidence_assessment": "insufficient",
          "evidence_count": 2,
          "freshness": "fresh",
          "made_at": "2026-01-15T16:00:00Z",
          "made_by": "sarah_chen",
          "rationale": "ADR 0004: Continuous PID loop with anti-windup clamping guarantees stability within +/- 0.4C of setpoint under heavy duty cycle.",
          "repo": "acme-eng/thermal-control-system",
          "repo_full_name": "acme-eng/thermal-control-system",
          "review_status": "auto_confirmed",
          "state": "accepted",
          "superseded_by_decision_id": null,
          "supersedes_decision_id": null,
          "title": "Adopt Discrete PID Controller for Chamber Temperature Regulation"
        },
        {
          "alternatives_considered": [],
          "alternatives_json": "[]",
          "confidence": 0.8,
          "decision_id": "dec_thermal_pid_01",
          "evidence_assessment": "insufficient",
          "evidence_count": 1,
          "freshness": "fresh",
          "made_at": "2026-01-15T16:00:00Z",
          "made_by": "sarah_chen",
          "rationale": "Governing architectural baseline decision",
          "repo": "acme-eng/thermal-control-system",
          "repo_full_name": "acme-eng/thermal-control-system",
          "review_status": "pending_review",
          "state": "accepted",
          "superseded_by_decision_id": null,
          "supersedes_decision_id": null,
          "title": "Architectural Decision dec_thermal_pid_01"
        },
        {
          "alternatives_considered": [
            {
              "description": "Deadband on-off threshold control +/- 1.5C",
              "evidence_event_ids": [
                "evt_rev_thermal_comm2"
              ],
              "rejection_reason": "Benchmarking revealed 17% higher latency and persistent 6.2C transient overshoot"
            }
          ],
          "alternatives_json": "[{\"description\": \"Deadband on-off threshold control +/- 1.5C\", \"rejection_reason\": \"Benchmarking revealed 17% higher latency and persistent 6.2C transient overshoot\", \"evidence_event_ids\": [\"evt_rev_thermal_comm2\"]}]",
          "confidence": 0.96,
          "decision_id": "dec_thermal_deadband_rejected",
          "evidence_assessment": "weak",
          "evidence_count": 2,
          "freshness": "fresh",
          "made_at": "2026-01-12T15:00:00Z",
          "made_by": "sarah_chen",
          "rationale": "Tested in simulation following Issue #12; deadband was insufficient to prevent emergency chamber thermal trip.",
          "repo": "acme-eng/thermal-control-system",
          "repo_full_name": "acme-eng/thermal-control-system",
          "review_status": "auto_confirmed",
          "state": "rejected",
          "superseded_by_decision_id": null,
          "supersedes_decision_id": null,
          "title": "Reject Simple Deadband Hysteresis for Thermal Control"
        },
        {
          "alternatives_considered": [],
          "alternatives_json": "[]",
          "confidence": 0.8,
          "decision_id": "dec_thermal_bangbang_02",
          "evidence_assessment": "insufficient",
          "evidence_count": 1,
          "freshness": "fresh",
          "made_at": "2026-01-12T15:00:00Z",
          "made_by": "sarah_chen",
          "rationale": "Governing architectural baseline decision",
          "repo": "acme-eng/thermal-control-system",
          "repo_full_name": "acme-eng/thermal-control-system",
          "review_status": "pending_review",
          "state": "rejected",
          "superseded_by_decision_id": null,
          "supersedes_decision_id": null,
          "title": "Architectural Decision dec_thermal_bangbang_02"
        }
      ],
      "status": "success"
    },
    "graph_all": {
      "data": {
        "links": [
          {
            "id": "edge_evidenced_by_dec_thermal_dead_evt_rev_thermal_",
            "is_active": true,
            "source": "dec_thermal_deadband_rejected",
            "target": "evt_rev_thermal_comm1",
            "type": "evidenced_by",
            "valid_from": "2026-01-12T15:00:00Z",
            "valid_to": null
          },
          {
            "id": "edge_affects_dec_thermal_dead_ent_file_acme-en",
            "is_active": true,
            "source": "dec_thermal_deadband_rejected",
            "target": "ent_file_acme-eng_thermal-control-system_src_thermal_control_py",
            "type": "affects",
            "valid_from": "2026-01-12T15:00:00Z",
            "valid_to": null
          },
          {
            "id": "edge_affects_dec_thermal_dead_ent_fn_acme-eng_",
            "is_active": true,
            "source": "dec_thermal_deadband_rejected",
            "target": "ent_fn_acme-eng_thermal-control-system_src_thermal_control_py_regulate_temperature",
            "type": "affects",
            "valid_from": "2026-01-12T15:00:00Z",
            "valid_to": null
          },
          {
            "id": "edge_evidenced_by_dec_thermal_pid__evt_adr_thermal_",
            "is_active": true,
            "source": "dec_thermal_pid_accepted",
            "target": "evt_adr_thermal_0004",
            "type": "evidenced_by",
            "valid_from": "2026-01-15T16:00:00Z",
            "valid_to": null
          },
          {
            "id": "edge_evidenced_by_dec_thermal_pid__evt_git_thermal_",
            "is_active": true,
            "source": "dec_thermal_pid_accepted",
            "target": "evt_git_thermal_a1b2c3d4",
            "type": "evidenced_by",
            "valid_from": "2026-01-15T16:00:00Z",
            "valid_to": null
          },
          {
            "id": "edge_affects_dec_thermal_pid__ent_file_acme-en",
            "is_active": true,
            "source": "dec_thermal_pid_accepted",
            "target": "ent_file_acme-eng_thermal-control-system_src_thermal_control_py",
            "type": "affects",
            "valid_from": "2026-01-15T16:00:00Z",
            "valid_to": null
          },
          {
            "id": "edge_affects_dec_thermal_pid__ent_fn_acme-eng_",
            "is_active": true,
            "source": "dec_thermal_pid_accepted",
            "target": "ent_fn_acme-eng_thermal-control-system_src_thermal_control_py_regulate_temperature",
            "type": "affects",
            "valid_from": "2026-01-15T16:00:00Z",
            "valid_to": null
          },
          {
            "id": "edge_affects_dec_thermal_pid__ent_dep_acme-eng",
            "is_active": true,
            "source": "dec_thermal_pid_accepted",
            "target": "ent_dep_acme-eng_thermal-control-system_scipy",
            "type": "affects",
            "valid_from": "2026-01-15T16:00:00Z",
            "valid_to": null
          },
          {
            "id": "edge_evidenced_by_dec_cache_local__evt_pr_cache_38",
            "is_active": false,
            "source": "dec_cache_local_lru_proposed",
            "target": "evt_pr_cache_38",
            "type": "evidenced_by",
            "valid_from": "2026-02-03T14:30:00Z",
            "valid_to": "2026-02-06T15:00:00Z"
          },
          {
            "id": "edge_affects_dec_cache_local__ent_file_acme-en",
            "is_active": false,
            "source": "dec_cache_local_lru_proposed",
            "target": "ent_file_acme-eng_distributed-cache-service_src_cache_store_py",
            "type": "affects",
            "valid_from": "2026-02-03T14:30:00Z",
            "valid_to": "2026-02-06T15:00:00Z"
          },
          {
            "id": "edge_affects_dec_cache_local__ent_fn_acme-eng_",
            "is_active": false,
            "source": "dec_cache_local_lru_proposed",
            "target": "ent_fn_acme-eng_distributed-cache-service_src_cache_store_py_cache_set",
            "type": "affects",
            "valid_from": "2026-02-03T14:30:00Z",
            "valid_to": "2026-02-06T15:00:00Z"
          },
          {
            "id": "edge_evidenced_by_dec_cache_redis__evt_adr_cache_00",
            "is_active": true,
            "source": "dec_cache_redis_accepted",
            "target": "evt_adr_cache_0009",
            "type": "evidenced_by",
            "valid_from": "2026-02-06T15:00:00Z",
            "valid_to": null
          },
          {
            "id": "edge_evidenced_by_dec_cache_redis__evt_rev_cache_c2",
            "is_active": true,
            "source": "dec_cache_redis_accepted",
            "target": "evt_rev_cache_c201",
            "type": "evidenced_by",
            "valid_from": "2026-02-06T15:00:00Z",
            "valid_to": null
          },
          {
            "id": "edge_affects_dec_cache_redis__ent_file_acme-en",
            "is_active": true,
            "source": "dec_cache_redis_accepted",
            "target": "ent_file_acme-eng_distributed-cache-service_src_cache_store_py",
            "type": "affects",
            "valid_from": "2026-02-06T15:00:00Z",
            "valid_to": null
          },
          {
            "id": "edge_affects_dec_cache_redis__ent_fn_acme-eng_",
            "is_active": true,
            "source": "dec_cache_redis_accepted",
            "target": "ent_fn_acme-eng_distributed-cache-service_src_cache_store_py_cache_set",
            "type": "affects",
            "valid_from": "2026-02-06T15:00:00Z",
            "valid_to": null
          },
          {
            "id": "edge_affects_dec_cache_redis__ent_dep_acme-eng",
            "is_active": true,
            "source": "dec_cache_redis_accepted",
            "target": "ent_dep_acme-eng_distributed-cache-service_redis",
            "type": "affects",
            "valid_from": "2026-02-06T15:00:00Z",
            "valid_to": null
          },
          {
            "id": "edge_supersedes_dec_cache_redis__dec_cache_local_",
            "is_active": false,
            "source": "dec_cache_redis_accepted",
            "target": "dec_cache_local_lru_proposed",
            "type": "supersedes",
            "valid_from": "2026-02-06T15:00:00Z",
            "valid_to": "2026-02-06T15:00:00Z"
          },
          {
            "id": "edge_super_dec_cache_redis_accepted_dec_cache_local_lru_proposed",
            "is_active": true,
            "source": "dec_cache_redis_accepted",
            "target": "dec_cache_local_lru_proposed",
            "type": "supersedes",
            "valid_from": "2026-02-06T15:00:00Z",
            "valid_to": null
          },
          {
            "id": "edge_conflicts_with_dec_cache_local__dec_cache_redis_",
            "is_active": true,
            "source": "dec_cache_local_lru_proposed",
            "target": "dec_cache_redis_accepted",
            "type": "conflicts_with",
            "valid_from": "2026-02-06T15:00:00Z",
            "valid_to": null
          }
        ],
        "nodes": [
          {
            "color": "#ef4444",
            "confidence": 0.96,
            "id": "dec_thermal_deadband_rejected",
            "label": "Reject Simple Deadband Hysteresis for Thermal Control",
            "made_at": "2026-01-12T15:00:00Z",
            "made_by": "sarah_chen",
            "repo": "acme-eng/thermal-control-system",
            "review_status": "auto_confirmed",
            "state": "rejected",
            "type": "decision"
          },
          {
            "color": "#10b981",
            "confidence": 0.98,
            "id": "dec_thermal_pid_accepted",
            "label": "Adopt Discrete PID Controller for Chamber Temperature Regulation",
            "made_at": "2026-01-15T16:00:00Z",
            "made_by": "sarah_chen",
            "repo": "acme-eng/thermal-control-system",
            "review_status": "auto_confirmed",
            "state": "accepted",
            "type": "decision"
          },
          {
            "color": "#8b5cf6",
            "confidence": 0.82,
            "id": "dec_cache_local_lru_proposed",
            "label": "Retain In-Memory LRU Cache with Process Memory Cap",
            "made_at": "2026-02-03T14:30:00Z",
            "made_by": "marcus_vance",
            "repo": "acme-eng/distributed-cache-service",
            "review_status": "pending_review",
            "state": "superseded",
            "type": "decision"
          },
          {
            "color": "#10b981",
            "confidence": 0.97,
            "id": "dec_cache_redis_accepted",
            "label": "Migrate from In-Memory LRU to Distributed Redis Cluster",
            "made_at": "2026-02-06T15:00:00Z",
            "made_by": "priya_patel",
            "repo": "acme-eng/distributed-cache-service",
            "review_status": "auto_confirmed",
            "state": "accepted",
            "type": "decision"
          },
          {
            "color": "#10b981",
            "confidence": 0.8,
            "id": "dec_thermal_pid_01",
            "label": "Architectural Decision dec_thermal_pid_01",
            "made_at": "2026-01-15T16:00:00Z",
            "made_by": "sarah_chen",
            "repo": "acme-eng/thermal-control-system",
            "review_status": "pending_review",
            "state": "accepted",
            "type": "decision"
          },
          {
            "color": "#ef4444",
            "confidence": 0.8,
            "id": "dec_thermal_bangbang_02",
            "label": "Architectural Decision dec_thermal_bangbang_02",
            "made_at": "2026-01-12T15:00:00Z",
            "made_by": "sarah_chen",
            "repo": "acme-eng/thermal-control-system",
            "review_status": "pending_review",
            "state": "rejected",
            "type": "decision"
          },
          {
            "color": "#10b981",
            "confidence": 0.8,
            "id": "dec_cache_redis_01",
            "label": "Architectural Decision dec_cache_redis_01",
            "made_at": "2026-02-06T15:00:00Z",
            "made_by": "priya_patel",
            "repo": "acme-eng/distributed-cache-service",
            "review_status": "pending_review",
            "state": "accepted",
            "type": "decision"
          },
          {
            "color": "#3b82f6",
            "entity_type": "file",
            "id": "ent_file_acme-eng_thermal-control-system_src_thermal_control_py",
            "label": "src/thermal/control.py",
            "repo": "acme-eng/thermal-control-system",
            "summary": "Core thermal regulation module",
            "type": "entity"
          },
          {
            "color": "#3b82f6",
            "entity_type": "function",
            "id": "ent_fn_acme-eng_thermal-control-system_src_thermal_control_py_regulate_temperature",
            "label": "src/thermal/control.py::regulate_temperature",
            "repo": "acme-eng/thermal-control-system",
            "summary": "Applies feedback loop control algorithm",
            "type": "entity"
          },
          {
            "color": "#3b82f6",
            "entity_type": "function",
            "id": "ent_fn_acme-eng_thermal-control-system_src_thermal_control_py_read_telemetry_sensor",
            "label": "src/thermal/control.py::read_telemetry_sensor",
            "repo": "acme-eng/thermal-control-system",
            "summary": "Reads raw temperature sensor hardware bus",
            "type": "entity"
          },
          {
            "color": "#3b82f6",
            "entity_type": "file",
            "id": "ent_file_acme-eng_thermal-control-system_docs_adr_0004-pid-thermal-regulation_md",
            "label": "docs/adr/0004-pid-thermal-regulation.md",
            "repo": "acme-eng/thermal-control-system",
            "summary": "ADR 0004 documentation",
            "type": "entity"
          },
          {
            "color": "#3b82f6",
            "entity_type": "dependency",
            "id": "ent_dep_acme-eng_thermal-control-system_scipy",
            "label": "deps::scipy",
            "repo": "acme-eng/thermal-control-system",
            "summary": "Dependency package scipy (==1.11.2)",
            "type": "entity"
          },
          {
            "color": "#3b82f6",
            "entity_type": "file",
            "id": "ent_file_acme-eng_distributed-cache-service_src_cache_store_py",
            "label": "src/cache/store.py",
            "repo": "acme-eng/distributed-cache-service",
            "summary": "Distributed caching implementation",
            "type": "entity"
          },
          {
            "color": "#3b82f6",
            "entity_type": "function",
            "id": "ent_fn_acme-eng_distributed-cache-service_src_cache_store_py_cache_get",
            "label": "src/cache/store.py::cache_get",
            "repo": "acme-eng/distributed-cache-service",
            "summary": "Fetch key from cache cluster",
            "type": "entity"
          },
          {
            "color": "#3b82f6",
            "entity_type": "function",
            "id": "ent_fn_acme-eng_distributed-cache-service_src_cache_store_py_cache_set",
            "label": "src/cache/store.py::cache_set",
            "repo": "acme-eng/distributed-cache-service",
            "summary": "Write key-value pair to cluster with TTL",
            "type": "entity"
          },
          {
            "color": "#3b82f6",
            "entity_type": "dependency",
            "id": "ent_dep_acme-eng_distributed-cache-service_redis",
            "label": "deps::redis",
            "repo": "acme-eng/distributed-cache-service",
            "summary": "Dependency package redis (==4.5.4)",
            "type": "entity"
          },
          {
            "author": "alex_rodriguez",
            "color": "#ec4899",
            "id": "evt_issue_thermal_12",
            "label": "#12: Severe chamber overheating observed under 80% duty cycle",
            "repo": "acme-eng/thermal-control-system",
            "source_type": "github_issue",
            "source_url": "https://github.com/acme-eng/thermal-control-system/issues/12",
            "timestamp": "2026-01-10T09:15:00Z",
            "type": "event"
          },
          {
            "author": "marcus_vance",
            "color": "#ec4899",
            "id": "evt_rev_thermal_comm1",
            "label": "Marcus on Issue #12: Proposed deadband tuning",
            "repo": "acme-eng/thermal-control-system",
            "source_type": "pr_review_comment",
            "source_url": "https://github.com/acme-eng/thermal-control-system/issues/12#issuecomment-101",
            "timestamp": "2026-01-11T11:20:00Z",
            "type": "event"
          },
          {
            "author": "sarah_chen",
            "color": "#ec4899",
            "id": "evt_rev_thermal_comm2",
            "label": "Sarah on Issue #12: Benchmark results against deadband tuning",
            "repo": "acme-eng/thermal-control-system",
            "source_type": "pr_review_comment",
            "source_url": "https://github.com/acme-eng/thermal-control-system/issues/12#issuecomment-102",
            "timestamp": "2026-01-12T14:45:00Z",
            "type": "event"
          },
          {
            "author": "sarah_chen",
            "color": "#ec4899",
            "id": "evt_adr_thermal_0004",
            "label": "ADR 0004: Adopt Discrete PID Algorithm for Thermal Regulation",
            "repo": "acme-eng/thermal-control-system",
            "source_type": "adr",
            "source_url": "https://github.com/acme-eng/thermal-control-system/blob/main/docs/adr/0004-pid-thermal-regulation.md",
            "timestamp": "2026-01-15T16:00:00Z",
            "type": "event"
          },
          {
            "author": "sarah_chen",
            "color": "#ec4899",
            "id": "evt_git_thermal_a1b2c3d4",
            "label": "feat(thermal): implement discrete PID controller with anti-windup (Closes #12)",
            "repo": "acme-eng/thermal-control-system",
            "source_type": "git_commit",
            "source_url": "https://github.com/acme-eng/thermal-control-system/commit/a1b2c3d4e5f67890",
            "timestamp": "2026-01-18T10:00:00Z",
            "type": "event"
          },
          {
            "author": "alex_rodriguez",
            "color": "#ec4899",
            "id": "evt_issue_cache_34",
            "label": "#34: Worker node OOMKilled under 50,000 req/sec spike",
            "repo": "acme-eng/distributed-cache-service",
            "source_type": "github_issue",
            "source_url": "https://github.com/acme-eng/distributed-cache-service/issues/34",
            "timestamp": "2026-02-01T10:00:00Z",
            "type": "event"
          },
          {
            "author": "marcus_vance",
            "color": "#ec4899",
            "id": "evt_pr_cache_38",
            "label": "PR #38: Add soft memory cap to in-memory LRU cache (Closes #34)",
            "repo": "acme-eng/distributed-cache-service",
            "source_type": "github_pr",
            "source_url": "https://github.com/acme-eng/distributed-cache-service/pull/38",
            "timestamp": "2026-02-03T14:30:00Z",
            "type": "event"
          },
          {
            "author": "priya_patel",
            "color": "#ec4899",
            "id": "evt_rev_cache_c201",
            "label": "Priya review on PR #38: In-memory cache cannot scale across replicas",
            "repo": "acme-eng/distributed-cache-service",
            "source_type": "pr_review_comment",
            "source_url": "https://github.com/acme-eng/distributed-cache-service/pull/38#discussion_r201",
            "timestamp": "2026-02-04T09:00:00Z",
            "type": "event"
          },
          {
            "author": "priya_patel",
            "color": "#ec4899",
            "id": "evt_adr_cache_0009",
            "label": "ADR 0009: Migrate to Redis Cluster for Distributed Caching",
            "repo": "acme-eng/distributed-cache-service",
            "source_type": "adr",
            "source_url": "https://github.com/acme-eng/distributed-cache-service/blob/main/docs/adr/0009-redis-cluster-cache.md",
            "timestamp": "2026-02-06T15:00:00Z",
            "type": "event"
          }
        ]
      },
      "status": "success"
    },
    "graph_cache": {
      "data": {
        "links": [
          {
            "id": "edge_evidenced_by_dec_cache_local__evt_pr_cache_38",
            "is_active": false,
            "source": "dec_cache_local_lru_proposed",
            "target": "evt_pr_cache_38",
            "type": "evidenced_by",
            "valid_from": "2026-02-03T14:30:00Z",
            "valid_to": "2026-02-06T15:00:00Z"
          },
          {
            "id": "edge_affects_dec_cache_local__ent_file_acme-en",
            "is_active": false,
            "source": "dec_cache_local_lru_proposed",
            "target": "ent_file_acme-eng_distributed-cache-service_src_cache_store_py",
            "type": "affects",
            "valid_from": "2026-02-03T14:30:00Z",
            "valid_to": "2026-02-06T15:00:00Z"
          },
          {
            "id": "edge_affects_dec_cache_local__ent_fn_acme-eng_",
            "is_active": false,
            "source": "dec_cache_local_lru_proposed",
            "target": "ent_fn_acme-eng_distributed-cache-service_src_cache_store_py_cache_set",
            "type": "affects",
            "valid_from": "2026-02-03T14:30:00Z",
            "valid_to": "2026-02-06T15:00:00Z"
          },
          {
            "id": "edge_evidenced_by_dec_cache_redis__evt_adr_cache_00",
            "is_active": true,
            "source": "dec_cache_redis_accepted",
            "target": "evt_adr_cache_0009",
            "type": "evidenced_by",
            "valid_from": "2026-02-06T15:00:00Z",
            "valid_to": null
          },
          {
            "id": "edge_evidenced_by_dec_cache_redis__evt_rev_cache_c2",
            "is_active": true,
            "source": "dec_cache_redis_accepted",
            "target": "evt_rev_cache_c201",
            "type": "evidenced_by",
            "valid_from": "2026-02-06T15:00:00Z",
            "valid_to": null
          },
          {
            "id": "edge_affects_dec_cache_redis__ent_file_acme-en",
            "is_active": true,
            "source": "dec_cache_redis_accepted",
            "target": "ent_file_acme-eng_distributed-cache-service_src_cache_store_py",
            "type": "affects",
            "valid_from": "2026-02-06T15:00:00Z",
            "valid_to": null
          },
          {
            "id": "edge_affects_dec_cache_redis__ent_fn_acme-eng_",
            "is_active": true,
            "source": "dec_cache_redis_accepted",
            "target": "ent_fn_acme-eng_distributed-cache-service_src_cache_store_py_cache_set",
            "type": "affects",
            "valid_from": "2026-02-06T15:00:00Z",
            "valid_to": null
          },
          {
            "id": "edge_affects_dec_cache_redis__ent_dep_acme-eng",
            "is_active": true,
            "source": "dec_cache_redis_accepted",
            "target": "ent_dep_acme-eng_distributed-cache-service_redis",
            "type": "affects",
            "valid_from": "2026-02-06T15:00:00Z",
            "valid_to": null
          },
          {
            "id": "edge_supersedes_dec_cache_redis__dec_cache_local_",
            "is_active": false,
            "source": "dec_cache_redis_accepted",
            "target": "dec_cache_local_lru_proposed",
            "type": "supersedes",
            "valid_from": "2026-02-06T15:00:00Z",
            "valid_to": "2026-02-06T15:00:00Z"
          },
          {
            "id": "edge_super_dec_cache_redis_accepted_dec_cache_local_lru_proposed",
            "is_active": true,
            "source": "dec_cache_redis_accepted",
            "target": "dec_cache_local_lru_proposed",
            "type": "supersedes",
            "valid_from": "2026-02-06T15:00:00Z",
            "valid_to": null
          },
          {
            "id": "edge_conflicts_with_dec_cache_local__dec_cache_redis_",
            "is_active": true,
            "source": "dec_cache_local_lru_proposed",
            "target": "dec_cache_redis_accepted",
            "type": "conflicts_with",
            "valid_from": "2026-02-06T15:00:00Z",
            "valid_to": null
          }
        ],
        "nodes": [
          {
            "color": "#8b5cf6",
            "confidence": 0.82,
            "id": "dec_cache_local_lru_proposed",
            "label": "Retain In-Memory LRU Cache with Process Memory Cap",
            "made_at": "2026-02-03T14:30:00Z",
            "made_by": "marcus_vance",
            "repo": "acme-eng/distributed-cache-service",
            "review_status": "pending_review",
            "state": "superseded",
            "type": "decision"
          },
          {
            "color": "#10b981",
            "confidence": 0.97,
            "id": "dec_cache_redis_accepted",
            "label": "Migrate from In-Memory LRU to Distributed Redis Cluster",
            "made_at": "2026-02-06T15:00:00Z",
            "made_by": "priya_patel",
            "repo": "acme-eng/distributed-cache-service",
            "review_status": "auto_confirmed",
            "state": "accepted",
            "type": "decision"
          },
          {
            "color": "#10b981",
            "confidence": 0.8,
            "id": "dec_cache_redis_01",
            "label": "Architectural Decision dec_cache_redis_01",
            "made_at": "2026-02-06T15:00:00Z",
            "made_by": "priya_patel",
            "repo": "acme-eng/distributed-cache-service",
            "review_status": "pending_review",
            "state": "accepted",
            "type": "decision"
          },
          {
            "color": "#3b82f6",
            "entity_type": "file",
            "id": "ent_file_acme-eng_distributed-cache-service_src_cache_store_py",
            "label": "src/cache/store.py",
            "repo": "acme-eng/distributed-cache-service",
            "summary": "Distributed caching implementation",
            "type": "entity"
          },
          {
            "color": "#3b82f6",
            "entity_type": "function",
            "id": "ent_fn_acme-eng_distributed-cache-service_src_cache_store_py_cache_get",
            "label": "src/cache/store.py::cache_get",
            "repo": "acme-eng/distributed-cache-service",
            "summary": "Fetch key from cache cluster",
            "type": "entity"
          },
          {
            "color": "#3b82f6",
            "entity_type": "function",
            "id": "ent_fn_acme-eng_distributed-cache-service_src_cache_store_py_cache_set",
            "label": "src/cache/store.py::cache_set",
            "repo": "acme-eng/distributed-cache-service",
            "summary": "Write key-value pair to cluster with TTL",
            "type": "entity"
          },
          {
            "color": "#3b82f6",
            "entity_type": "dependency",
            "id": "ent_dep_acme-eng_distributed-cache-service_redis",
            "label": "deps::redis",
            "repo": "acme-eng/distributed-cache-service",
            "summary": "Dependency package redis (==4.5.4)",
            "type": "entity"
          },
          {
            "author": "alex_rodriguez",
            "color": "#ec4899",
            "id": "evt_issue_cache_34",
            "label": "#34: Worker node OOMKilled under 50,000 req/sec spike",
            "repo": "acme-eng/distributed-cache-service",
            "source_type": "github_issue",
            "source_url": "https://github.com/acme-eng/distributed-cache-service/issues/34",
            "timestamp": "2026-02-01T10:00:00Z",
            "type": "event"
          },
          {
            "author": "marcus_vance",
            "color": "#ec4899",
            "id": "evt_pr_cache_38",
            "label": "PR #38: Add soft memory cap to in-memory LRU cache (Closes #34)",
            "repo": "acme-eng/distributed-cache-service",
            "source_type": "github_pr",
            "source_url": "https://github.com/acme-eng/distributed-cache-service/pull/38",
            "timestamp": "2026-02-03T14:30:00Z",
            "type": "event"
          },
          {
            "author": "priya_patel",
            "color": "#ec4899",
            "id": "evt_rev_cache_c201",
            "label": "Priya review on PR #38: In-memory cache cannot scale across replicas",
            "repo": "acme-eng/distributed-cache-service",
            "source_type": "pr_review_comment",
            "source_url": "https://github.com/acme-eng/distributed-cache-service/pull/38#discussion_r201",
            "timestamp": "2026-02-04T09:00:00Z",
            "type": "event"
          },
          {
            "author": "priya_patel",
            "color": "#ec4899",
            "id": "evt_adr_cache_0009",
            "label": "ADR 0009: Migrate to Redis Cluster for Distributed Caching",
            "repo": "acme-eng/distributed-cache-service",
            "source_type": "adr",
            "source_url": "https://github.com/acme-eng/distributed-cache-service/blob/main/docs/adr/0009-redis-cluster-cache.md",
            "timestamp": "2026-02-06T15:00:00Z",
            "type": "event"
          }
        ]
      },
      "status": "success"
    },
    "graph_thermal": {
      "data": {
        "links": [
          {
            "id": "edge_evidenced_by_dec_thermal_dead_evt_rev_thermal_",
            "is_active": true,
            "source": "dec_thermal_deadband_rejected",
            "target": "evt_rev_thermal_comm1",
            "type": "evidenced_by",
            "valid_from": "2026-01-12T15:00:00Z",
            "valid_to": null
          },
          {
            "id": "edge_affects_dec_thermal_dead_ent_file_acme-en",
            "is_active": true,
            "source": "dec_thermal_deadband_rejected",
            "target": "ent_file_acme-eng_thermal-control-system_src_thermal_control_py",
            "type": "affects",
            "valid_from": "2026-01-12T15:00:00Z",
            "valid_to": null
          },
          {
            "id": "edge_affects_dec_thermal_dead_ent_fn_acme-eng_",
            "is_active": true,
            "source": "dec_thermal_deadband_rejected",
            "target": "ent_fn_acme-eng_thermal-control-system_src_thermal_control_py_regulate_temperature",
            "type": "affects",
            "valid_from": "2026-01-12T15:00:00Z",
            "valid_to": null
          },
          {
            "id": "edge_evidenced_by_dec_thermal_pid__evt_adr_thermal_",
            "is_active": true,
            "source": "dec_thermal_pid_accepted",
            "target": "evt_adr_thermal_0004",
            "type": "evidenced_by",
            "valid_from": "2026-01-15T16:00:00Z",
            "valid_to": null
          },
          {
            "id": "edge_evidenced_by_dec_thermal_pid__evt_git_thermal_",
            "is_active": true,
            "source": "dec_thermal_pid_accepted",
            "target": "evt_git_thermal_a1b2c3d4",
            "type": "evidenced_by",
            "valid_from": "2026-01-15T16:00:00Z",
            "valid_to": null
          },
          {
            "id": "edge_affects_dec_thermal_pid__ent_file_acme-en",
            "is_active": true,
            "source": "dec_thermal_pid_accepted",
            "target": "ent_file_acme-eng_thermal-control-system_src_thermal_control_py",
            "type": "affects",
            "valid_from": "2026-01-15T16:00:00Z",
            "valid_to": null
          },
          {
            "id": "edge_affects_dec_thermal_pid__ent_fn_acme-eng_",
            "is_active": true,
            "source": "dec_thermal_pid_accepted",
            "target": "ent_fn_acme-eng_thermal-control-system_src_thermal_control_py_regulate_temperature",
            "type": "affects",
            "valid_from": "2026-01-15T16:00:00Z",
            "valid_to": null
          },
          {
            "id": "edge_affects_dec_thermal_pid__ent_dep_acme-eng",
            "is_active": true,
            "source": "dec_thermal_pid_accepted",
            "target": "ent_dep_acme-eng_thermal-control-system_scipy",
            "type": "affects",
            "valid_from": "2026-01-15T16:00:00Z",
            "valid_to": null
          }
        ],
        "nodes": [
          {
            "color": "#ef4444",
            "confidence": 0.96,
            "id": "dec_thermal_deadband_rejected",
            "label": "Reject Simple Deadband Hysteresis for Thermal Control",
            "made_at": "2026-01-12T15:00:00Z",
            "made_by": "sarah_chen",
            "repo": "acme-eng/thermal-control-system",
            "review_status": "auto_confirmed",
            "state": "rejected",
            "type": "decision"
          },
          {
            "color": "#10b981",
            "confidence": 0.98,
            "id": "dec_thermal_pid_accepted",
            "label": "Adopt Discrete PID Controller for Chamber Temperature Regulation",
            "made_at": "2026-01-15T16:00:00Z",
            "made_by": "sarah_chen",
            "repo": "acme-eng/thermal-control-system",
            "review_status": "auto_confirmed",
            "state": "accepted",
            "type": "decision"
          },
          {
            "color": "#10b981",
            "confidence": 0.8,
            "id": "dec_thermal_pid_01",
            "label": "Architectural Decision dec_thermal_pid_01",
            "made_at": "2026-01-15T16:00:00Z",
            "made_by": "sarah_chen",
            "repo": "acme-eng/thermal-control-system",
            "review_status": "pending_review",
            "state": "accepted",
            "type": "decision"
          },
          {
            "color": "#ef4444",
            "confidence": 0.8,
            "id": "dec_thermal_bangbang_02",
            "label": "Architectural Decision dec_thermal_bangbang_02",
            "made_at": "2026-01-12T15:00:00Z",
            "made_by": "sarah_chen",
            "repo": "acme-eng/thermal-control-system",
            "review_status": "pending_review",
            "state": "rejected",
            "type": "decision"
          },
          {
            "color": "#3b82f6",
            "entity_type": "file",
            "id": "ent_file_acme-eng_thermal-control-system_src_thermal_control_py",
            "label": "src/thermal/control.py",
            "repo": "acme-eng/thermal-control-system",
            "summary": "Core thermal regulation module",
            "type": "entity"
          },
          {
            "color": "#3b82f6",
            "entity_type": "function",
            "id": "ent_fn_acme-eng_thermal-control-system_src_thermal_control_py_regulate_temperature",
            "label": "src/thermal/control.py::regulate_temperature",
            "repo": "acme-eng/thermal-control-system",
            "summary": "Applies feedback loop control algorithm",
            "type": "entity"
          },
          {
            "color": "#3b82f6",
            "entity_type": "function",
            "id": "ent_fn_acme-eng_thermal-control-system_src_thermal_control_py_read_telemetry_sensor",
            "label": "src/thermal/control.py::read_telemetry_sensor",
            "repo": "acme-eng/thermal-control-system",
            "summary": "Reads raw temperature sensor hardware bus",
            "type": "entity"
          },
          {
            "color": "#3b82f6",
            "entity_type": "file",
            "id": "ent_file_acme-eng_thermal-control-system_docs_adr_0004-pid-thermal-regulation_md",
            "label": "docs/adr/0004-pid-thermal-regulation.md",
            "repo": "acme-eng/thermal-control-system",
            "summary": "ADR 0004 documentation",
            "type": "entity"
          },
          {
            "color": "#3b82f6",
            "entity_type": "dependency",
            "id": "ent_dep_acme-eng_thermal-control-system_scipy",
            "label": "deps::scipy",
            "repo": "acme-eng/thermal-control-system",
            "summary": "Dependency package scipy (==1.11.2)",
            "type": "entity"
          },
          {
            "author": "alex_rodriguez",
            "color": "#ec4899",
            "id": "evt_issue_thermal_12",
            "label": "#12: Severe chamber overheating observed under 80% duty cycle",
            "repo": "acme-eng/thermal-control-system",
            "source_type": "github_issue",
            "source_url": "https://github.com/acme-eng/thermal-control-system/issues/12",
            "timestamp": "2026-01-10T09:15:00Z",
            "type": "event"
          },
          {
            "author": "marcus_vance",
            "color": "#ec4899",
            "id": "evt_rev_thermal_comm1",
            "label": "Marcus on Issue #12: Proposed deadband tuning",
            "repo": "acme-eng/thermal-control-system",
            "source_type": "pr_review_comment",
            "source_url": "https://github.com/acme-eng/thermal-control-system/issues/12#issuecomment-101",
            "timestamp": "2026-01-11T11:20:00Z",
            "type": "event"
          },
          {
            "author": "sarah_chen",
            "color": "#ec4899",
            "id": "evt_rev_thermal_comm2",
            "label": "Sarah on Issue #12: Benchmark results against deadband tuning",
            "repo": "acme-eng/thermal-control-system",
            "source_type": "pr_review_comment",
            "source_url": "https://github.com/acme-eng/thermal-control-system/issues/12#issuecomment-102",
            "timestamp": "2026-01-12T14:45:00Z",
            "type": "event"
          },
          {
            "author": "sarah_chen",
            "color": "#ec4899",
            "id": "evt_adr_thermal_0004",
            "label": "ADR 0004: Adopt Discrete PID Algorithm for Thermal Regulation",
            "repo": "acme-eng/thermal-control-system",
            "source_type": "adr",
            "source_url": "https://github.com/acme-eng/thermal-control-system/blob/main/docs/adr/0004-pid-thermal-regulation.md",
            "timestamp": "2026-01-15T16:00:00Z",
            "type": "event"
          },
          {
            "author": "sarah_chen",
            "color": "#ec4899",
            "id": "evt_git_thermal_a1b2c3d4",
            "label": "feat(thermal): implement discrete PID controller with anti-windup (Closes #12)",
            "repo": "acme-eng/thermal-control-system",
            "source_type": "git_commit",
            "source_url": "https://github.com/acme-eng/thermal-control-system/commit/a1b2c3d4e5f67890",
            "timestamp": "2026-01-18T10:00:00Z",
            "type": "event"
          }
        ]
      },
      "status": "success"
    },
    "guard_rules": {
      "data": [
        {
          "applies_to": [
            "src/thermal/**/*.py",
            "src/thermal/control.py"
          ],
          "approved_at": "2026-01-15T16:00:00Z",
          "approved_by": "sarah_chen",
          "created_at": "2026-10-23T10:21:13.087815+00:00",
          "created_by": "system",
          "decision_id": "dec_thermal_pid_01",
          "decision_title": "Architectural Decision dec_thermal_pid_01",
          "params": {
            "message": "Reintroduces rejected bang-bang threshold control or bypasses PID",
            "paths": [
              "src/thermal/**/*.py",
              "src/thermal/control.py"
            ],
            "regex": "\\b(on_off|threshold|hysteresis|bang_bang|on_off_relay)\\b"
          },
          "params_json": "{\"regex\": \"\\\\b(on_off|threshold|hysteresis|bang_bang|on_off_relay)\\\\b\", \"paths\": [\"src/thermal/**/*.py\", \"src/thermal/control.py\"], \"message\": \"Reintroduces rejected bang-bang threshold control or bypasses PID\"}",
          "polarity": "must_not",
          "repo": "acme-eng/thermal-control-system",
          "repo_full_name": "acme-eng/thermal-control-system",
          "rule_id": "rule_constraint_thermal_pid_01",
          "rule_type": "forbid_pattern",
          "source": "human",
          "status": "active"
        },
        {
          "applies_to": [
            "src/thermal/**/*.py",
            "src/thermal/control.py"
          ],
          "approved_at": "2026-01-12T15:00:00Z",
          "approved_by": "sarah_chen",
          "created_at": "2026-10-23T10:21:13.087815+00:00",
          "created_by": "system",
          "decision_id": "dec_thermal_bangbang_02",
          "decision_title": "Architectural Decision dec_thermal_bangbang_02",
          "params": {
            "message": "Reintroduces rejected bang-bang control loop",
            "paths": [
              "src/thermal/**/*.py",
              "src/thermal/control.py"
            ],
            "regex": "\\b(on_off_relay|bang_bang)\\b"
          },
          "params_json": "{\"regex\": \"\\\\b(on_off_relay|bang_bang)\\\\b\", \"paths\": [\"src/thermal/**/*.py\", \"src/thermal/control.py\"], \"message\": \"Reintroduces rejected bang-bang control loop\"}",
          "polarity": "must_not",
          "repo": "acme-eng/thermal-control-system",
          "repo_full_name": "acme-eng/thermal-control-system",
          "rule_id": "rule_constraint_thermal_bangbang_02",
          "rule_type": "forbid_pattern",
          "source": "human",
          "status": "active"
        },
        {
          "applies_to": [
            "src/cache/**/*.py",
            "src/cache/store.py"
          ],
          "approved_at": "2026-02-06T15:00:00Z",
          "approved_by": "priya_patel",
          "created_at": "2026-10-23T10:21:13.087815+00:00",
          "created_by": "system",
          "decision_id": "dec_cache_redis_01",
          "decision_title": "Architectural Decision dec_cache_redis_01",
          "params": {
            "message": "Reintroduces in-memory cache defying Redis cluster decision",
            "paths": [
              "src/cache/**/*.py",
              "src/cache/store.py"
            ],
            "regex": "(?:dict_cache\\s*=|local_cache\\s*=|cache_store\\s*=)"
          },
          "params_json": "{\"regex\": \"(?:dict_cache\\\\s*=|local_cache\\\\s*=|cache_store\\\\s*=)\", \"paths\": [\"src/cache/**/*.py\", \"src/cache/store.py\"], \"message\": \"Reintroduces in-memory cache defying Redis cluster decision\"}",
          "polarity": "must_not",
          "repo": "acme-eng/distributed-cache-service",
          "repo_full_name": "acme-eng/distributed-cache-service",
          "rule_id": "rule_constraint_cache_redis_01",
          "rule_type": "forbid_pattern",
          "source": "human",
          "status": "active"
        },
        {
          "applies_to": [
            "src/cache/**/*.py"
          ],
          "approved_at": "2026-02-06T15:00:00Z",
          "approved_by": "priya_patel",
          "created_at": "2026-02-06T15:00:00Z",
          "created_by": "rule_synthesizer",
          "decision_id": "dec_cache_redis_accepted",
          "decision_title": "Migrate from In-Memory LRU to Distributed Redis Cluster",
          "params": {
            "module": "redis",
            "paths": [
              "src/cache/**/*.py"
            ]
          },
          "params_json": "{\"module\": \"redis\", \"paths\": [\"src/cache/**/*.py\"]}",
          "polarity": "must",
          "repo": "acme-eng/distributed-cache-service",
          "repo_full_name": "acme-eng/distributed-cache-service",
          "rule_id": "rule_require_import_dec_cach_redis",
          "rule_type": "require_import",
          "source": "human",
          "status": "active"
        },
        {
          "applies_to": [
            "src/thermal/**/*.py",
            "**/control.py"
          ],
          "approved_at": "2026-01-15T16:00:00Z",
          "approved_by": "sarah_chen",
          "created_at": "2026-01-15T16:00:00Z",
          "created_by": "rule_synthesizer",
          "decision_id": "dec_thermal_pid_accepted",
          "decision_title": "Adopt Discrete PID Controller for Chamber Temperature Regulation",
          "params": {
            "message": "Reintroduces rejected bang-bang threshold hysteresis",
            "paths": [
              "src/thermal/**/*.py",
              "**/control.py"
            ],
            "regex": "(?:on_off_relay|threshold_high|hysteresis_loop|bang_bang)"
          },
          "params_json": "{\"regex\": \"(?:on_off_relay|threshold_high|hysteresis_loop|bang_bang)\", \"paths\": [\"src/thermal/**/*.py\", \"**/control.py\"], \"message\": \"Reintroduces rejected bang-bang threshold hysteresis\"}",
          "polarity": "must_not",
          "repo": "acme-eng/thermal-control-system",
          "repo_full_name": "acme-eng/thermal-control-system",
          "rule_id": "rule_forbid_pattern_dec_ther_bangbang",
          "rule_type": "forbid_pattern",
          "source": "human",
          "status": "active"
        }
      ],
      "status": "success"
    },
    "onboarding_cache": {
      "checklist": [
        {
          "category": "overview",
          "completed": false,
          "id": "chk_overview_01",
          "title": "Review Subsystem Architecture & Key Artifacts for Cache"
        },
        {
          "category": "active_decision",
          "completed": false,
          "decision_id": "dec_cache_redis_accepted",
          "id": "chk_dec_dec_cache_redis_accepted",
          "title": "Study Decision: Migrate from In-Memory LRU to Distributed Redis Cluster"
        },
        {
          "category": "active_decision",
          "completed": false,
          "decision_id": "dec_cache_redis_01",
          "id": "chk_dec_dec_cache_redis_01",
          "title": "Study Decision: Architectural Decision dec_cache_redis_01"
        },
        {
          "category": "superseded",
          "completed": false,
          "decision_id": "dec_cache_local_lru_proposed",
          "id": "chk_pitfall_dec_cache_local_lru_proposed",
          "title": "Superseded Architecture: Retain In-Memory LRU Cache with Process Memory Cap"
        },
        {
          "category": "evidence",
          "completed": false,
          "id": "chk_evidence_docs",
          "title": "Read Core ADRs and Design PRs (3 references)"
        }
      ],
      "files": [
        "src/cache/store.py"
      ],
      "module": "cache",
      "repo": "acme-eng/distributed-cache-service",
      "role": "Infrastructure / SRE",
      "sections": {
        "active_decisions": [
          {
            "assumptions": [],
            "citations": [
              {
                "author": "priya_patel",
                "event_id": "evt_adr_cache_0009",
                "source_type": "adr",
                "source_url": "https://github.com/acme-eng/distributed-cache-service/blob/main/docs/adr/0009-redis-cluster-cache.md",
                "title": "ADR 0009: Migrate to Redis Cluster for Distributed Caching"
              },
              {
                "author": "priya_patel",
                "event_id": "evt_rev_cache_c201",
                "source_type": "pr_review_comment",
                "source_url": "https://github.com/acme-eng/distributed-cache-service/pull/38#discussion_r201",
                "title": "Priya review on PR #38: In-memory cache cannot scale across replicas"
              }
            ],
            "decision_id": "dec_cache_redis_accepted",
            "evidence_label": "insufficient",
            "made_at": "2026-02-06T15:00:00Z",
            "made_by": "priya_patel",
            "rationale": "ADR 0009: Decommission local in-memory dict and migrate to Redis cluster to prevent container OOMs and maintain cache consistency across autoscaled pods.",
            "state": "accepted",
            "title": "Migrate from In-Memory LRU to Distributed Redis Cluster"
          },
          {
            "assumptions": [],
            "citations": [
              {
                "author": "priya_patel",
                "event_id": "evt_adr_cache_0009",
                "source_type": "adr",
                "source_url": "https://github.com/acme-eng/distributed-cache-service/blob/main/docs/adr/0009-redis-cluster-cache.md",
                "title": "ADR 0009: Migrate to Redis Cluster for Distributed Caching"
              }
            ],
            "decision_id": "dec_cache_redis_01",
            "evidence_label": "insufficient",
            "made_at": "2026-02-06T15:00:00Z",
            "made_by": "priya_patel",
            "rationale": "Governing architectural baseline decision",
            "state": "accepted",
            "title": "Architectural Decision dec_cache_redis_01"
          }
        ],
        "architectural_evidence": [
          {
            "author": "priya_patel",
            "event_id": "evt_adr_cache_0009",
            "source_type": "adr",
            "source_url": "https://github.com/acme-eng/distributed-cache-service/blob/main/docs/adr/0009-redis-cluster-cache.md",
            "summary": "Status: accepted\n\nContext:\nIn-memory LRU caching caused node OOM crashes (#34) and replica cache incoherence. PR #38 attempted local memory capping but was rejected because container autoscaling requires shared cache state.\n\nDecision:\nDecommission in",
            "timestamp": null,
            "title": "ADR 0009: Migrate to Redis Cluster for Distributed Caching"
          },
          {
            "author": "priya_patel",
            "event_id": "evt_rev_cache_c201",
            "source_type": "pr_review_comment",
            "source_url": "https://github.com/acme-eng/distributed-cache-service/pull/38#discussion_r201",
            "summary": "Local LRU will never solve cache stampedes across multiple container replicas. Each pod will maintain cold caches. We need a distributed Redis cluster.",
            "timestamp": null,
            "title": "Priya review on PR #38: In-memory cache cannot scale across replicas"
          },
          {
            "author": "marcus_vance",
            "event_id": "evt_pr_cache_38",
            "source_type": "github_pr",
            "source_url": "https://github.com/acme-eng/distributed-cache-service/pull/38",
            "summary": "Adds a maximum memory threshold to local Python process memory before aggressive eviction. Keeps caching local with sub-millisecond access.",
            "timestamp": null,
            "title": "PR #38: Add soft memory cap to in-memory LRU cache (Closes #34)"
          }
        ],
        "open_stale_items": [],
        "overview": {
          "affected_artifacts": [
            "src/cache/store.py",
            "src/cache/store.py::cache_get",
            "src/cache/store.py::cache_set"
          ],
          "module": "cache",
          "primary_architects": [
            "priya_patel",
            "marcus_vance"
          ],
          "role": "Infrastructure / SRE",
          "summary": "Onboarding guide for Cache in repository 'acme-eng/distributed-cache-service'. Contains 3 relevant architectural decisions curated for Infrastructure / SRE.",
          "task": "",
          "title": "Cache Architectural Onboarding (Infrastructure / SRE)",
          "total_relevant_decisions": 3
        },
        "rejected_pitfalls": [
          {
            "citations": [
              {
                "author": "marcus_vance",
                "event_id": "evt_pr_cache_38",
                "source_type": "github_pr",
                "source_url": "https://github.com/acme-eng/distributed-cache-service/pull/38",
                "title": "PR #38: Add soft memory cap to in-memory LRU cache (Closes #34)"
              }
            ],
            "decision_id": "dec_cache_local_lru_proposed",
            "rejected_by": "marcus_vance",
            "rejection_reason": "Keep cache strictly inside Python heap to guarantee sub-millisecond access and avoid external Redis infra.",
            "title": "Superseded Architecture: Retain In-Memory LRU Cache with Process Memory Cap"
          }
        ]
      },
      "status": "success",
      "task": "",
      "total_items": 5
    },
    "onboarding_thermal": {
      "checklist": [
        {
          "category": "overview",
          "completed": false,
          "id": "chk_overview_01",
          "title": "Review Subsystem Architecture & Key Artifacts for Thermal"
        },
        {
          "category": "active_decision",
          "completed": false,
          "decision_id": "dec_thermal_pid_accepted",
          "id": "chk_dec_dec_thermal_pid_accepted",
          "title": "Study Decision: Adopt Discrete PID Controller for Chamber Temperature Regulation"
        },
        {
          "category": "active_decision",
          "completed": false,
          "decision_id": "dec_thermal_pid_01",
          "id": "chk_dec_dec_thermal_pid_01",
          "title": "Study Decision: Architectural Decision dec_thermal_pid_01"
        },
        {
          "category": "pitfall",
          "completed": false,
          "decision_id": "dec_thermal_deadband_rejected",
          "id": "chk_pitfall_dec_thermal_deadband_rejected",
          "title": "Avoid Pitfall: Reject Simple Deadband Hysteresis for Thermal Control"
        },
        {
          "category": "pitfall",
          "completed": false,
          "decision_id": "dec_thermal_bangbang_02",
          "id": "chk_pitfall_dec_thermal_bangbang_02",
          "title": "Avoid Pitfall: Architectural Decision dec_thermal_bangbang_02"
        },
        {
          "category": "evidence",
          "completed": false,
          "id": "chk_evidence_docs",
          "title": "Read Core ADRs and Design PRs (4 references)"
        }
      ],
      "files": [
        "src/thermal/control.py"
      ],
      "module": "thermal",
      "repo": "acme-eng/thermal-control-system",
      "role": "Control Systems Engineer",
      "sections": {
        "active_decisions": [
          {
            "assumptions": [],
            "citations": [
              {
                "author": "sarah_chen",
                "event_id": "evt_adr_thermal_0004",
                "source_type": "adr",
                "source_url": "https://github.com/acme-eng/thermal-control-system/blob/main/docs/adr/0004-pid-thermal-regulation.md",
                "title": "ADR 0004: Adopt Discrete PID Algorithm for Thermal Regulation"
              },
              {
                "author": "sarah_chen",
                "event_id": "evt_git_thermal_a1b2c3d4",
                "source_type": "git_commit",
                "source_url": "https://github.com/acme-eng/thermal-control-system/commit/a1b2c3d4e5f67890",
                "title": "feat(thermal): implement discrete PID controller with anti-windup (Closes #12)"
              }
            ],
            "decision_id": "dec_thermal_pid_accepted",
            "evidence_label": "insufficient",
            "made_at": "2026-01-15T16:00:00Z",
            "made_by": "sarah_chen",
            "rationale": "ADR 0004: Continuous PID loop with anti-windup clamping guarantees stability within +/- 0.4C of setpoint under heavy duty cycle.",
            "state": "accepted",
            "title": "Adopt Discrete PID Controller for Chamber Temperature Regulation"
          },
          {
            "assumptions": [],
            "citations": [
              {
                "author": "sarah_chen",
                "event_id": "evt_rev_thermal_comm2",
                "source_type": "pr_review_comment",
                "source_url": "https://github.com/acme-eng/thermal-control-system/issues/12#issuecomment-102",
                "title": "Sarah on Issue #12: Benchmark results against deadband tuning"
              }
            ],
            "decision_id": "dec_thermal_pid_01",
            "evidence_label": "insufficient",
            "made_at": "2026-01-15T16:00:00Z",
            "made_by": "sarah_chen",
            "rationale": "Governing architectural baseline decision",
            "state": "accepted",
            "title": "Architectural Decision dec_thermal_pid_01"
          }
        ],
        "architectural_evidence": [
          {
            "author": "sarah_chen",
            "event_id": "evt_adr_thermal_0004",
            "source_type": "adr",
            "source_url": "https://github.com/acme-eng/thermal-control-system/blob/main/docs/adr/0004-pid-thermal-regulation.md",
            "summary": "Status: accepted\n\nContext:\nPrevious bang-bang / on-off controller caused severe thermal oscillations and triggered chamber shutdown (Issue #12). Deadband tuning was tested and rejected because it increased control latency by 17% and failed transient ",
            "timestamp": null,
            "title": "ADR 0004: Adopt Discrete PID Algorithm for Thermal Regulation"
          },
          {
            "author": "sarah_chen",
            "event_id": "evt_git_thermal_a1b2c3d4",
            "source_type": "git_commit",
            "source_url": "https://github.com/acme-eng/thermal-control-system/commit/a1b2c3d4e5f67890",
            "summary": "Replaces on-off controller with discrete PID controller. Implements ADR 0004. Closes #12.",
            "timestamp": null,
            "title": "feat(thermal): implement discrete PID controller with anti-windup (Closes #12)"
          },
          {
            "author": "sarah_chen",
            "event_id": "evt_rev_thermal_comm2",
            "source_type": "pr_review_comment",
            "source_url": "https://github.com/acme-eng/thermal-control-system/issues/12#issuecomment-102",
            "summary": "I benchmarked deadband tuning in simulation. It increased latency by 17% and still caused a 6.2C overshoot on rapid thermal transient. We must reject on-off hysteresis and move to continuous PID control.",
            "timestamp": null,
            "title": "Sarah on Issue #12: Benchmark results against deadband tuning"
          },
          {
            "author": "marcus_vance",
            "event_id": "evt_rev_thermal_comm1",
            "source_type": "pr_review_comment",
            "source_url": "https://github.com/acme-eng/thermal-control-system/issues/12#issuecomment-101",
            "summary": "We could tighten the deadband on the simple threshold on-off controller to +/- 1.5C. That requires zero external math libraries.",
            "timestamp": null,
            "title": "Marcus on Issue #12: Proposed deadband tuning"
          }
        ],
        "open_stale_items": [],
        "overview": {
          "affected_artifacts": [
            "src/thermal/control.py",
            "src/thermal/control.py::regulate_temperature",
            "src/thermal/control.py::read_telemetry_sensor",
            "docs/adr/0004-pid-thermal-regulation.md"
          ],
          "module": "thermal",
          "primary_architects": [
            "sarah_chen"
          ],
          "role": "Control Systems Engineer",
          "summary": "Onboarding guide for Thermal in repository 'acme-eng/thermal-control-system'. Contains 4 relevant architectural decisions curated for Control Systems Engineer.",
          "task": "",
          "title": "Thermal Architectural Onboarding (Control Systems Engineer)",
          "total_relevant_decisions": 4
        },
        "rejected_pitfalls": [
          {
            "citations": [
              {
                "author": "marcus_vance",
                "event_id": "evt_rev_thermal_comm1",
                "source_type": "pr_review_comment",
                "source_url": "https://github.com/acme-eng/thermal-control-system/issues/12#issuecomment-101",
                "title": "Marcus on Issue #12: Proposed deadband tuning"
              },
              {
                "author": "sarah_chen",
                "event_id": "evt_rev_thermal_comm2",
                "source_type": "pr_review_comment",
                "source_url": "https://github.com/acme-eng/thermal-control-system/issues/12#issuecomment-102",
                "title": "Sarah on Issue #12: Benchmark results against deadband tuning"
              }
            ],
            "decision_id": "dec_thermal_deadband_rejected",
            "rejected_by": "sarah_chen",
            "rejection_reason": "Tested in simulation following Issue #12; deadband was insufficient to prevent emergency chamber thermal trip.",
            "title": "Avoid Pitfall: Reject Simple Deadband Hysteresis for Thermal Control"
          },
          {
            "citations": [
              {
                "author": "sarah_chen",
                "event_id": "evt_rev_thermal_comm2",
                "source_type": "pr_review_comment",
                "source_url": "https://github.com/acme-eng/thermal-control-system/issues/12#issuecomment-102",
                "title": "Sarah on Issue #12: Benchmark results against deadband tuning"
              }
            ],
            "decision_id": "dec_thermal_bangbang_02",
            "rejected_by": "sarah_chen",
            "rejection_reason": "Governing architectural baseline decision",
            "title": "Avoid Pitfall: Architectural Decision dec_thermal_bangbang_02"
          }
        ]
      },
      "status": "success",
      "task": "",
      "total_items": 6
    },
    "repos": {
      "data": [
        "acme-eng/distributed-cache-service",
        "acme-eng/thermal-control-system"
      ],
      "status": "success"
    },
    "review_queue": {
      "data": [
        {
          "alternatives_json": "[]",
          "confidence": 0.8,
          "decision_id": "dec_thermal_pid_01",
          "evidence_assessment": "insufficient",
          "freshness": "fresh",
          "item_type": "decision",
          "made_at": "2026-01-15T16:00:00Z",
          "made_by": "sarah_chen",
          "queue_reason": "Evidence quality assessed as 'insufficient': missing evidence links or corroboration",
          "rationale": "Governing architectural baseline decision",
          "repo": "acme-eng/thermal-control-system",
          "repo_full_name": "acme-eng/thermal-control-system",
          "review_status": "pending_review",
          "state": "accepted",
          "superseded_by_decision_id": null,
          "supersedes_decision_id": null,
          "title": "Architectural Decision dec_thermal_pid_01"
        },
        {
          "alternatives_json": "[]",
          "confidence": 0.8,
          "decision_id": "dec_thermal_bangbang_02",
          "evidence_assessment": "insufficient",
          "freshness": "fresh",
          "item_type": "decision",
          "made_at": "2026-01-12T15:00:00Z",
          "made_by": "sarah_chen",
          "queue_reason": "Evidence quality assessed as 'insufficient': missing evidence links or corroboration",
          "rationale": "Governing architectural baseline decision",
          "repo": "acme-eng/thermal-control-system",
          "repo_full_name": "acme-eng/thermal-control-system",
          "review_status": "pending_review",
          "state": "rejected",
          "superseded_by_decision_id": null,
          "supersedes_decision_id": null,
          "title": "Architectural Decision dec_thermal_bangbang_02"
        },
        {
          "alternatives_json": "[]",
          "confidence": 0.8,
          "decision_id": "dec_cache_redis_01",
          "evidence_assessment": "insufficient",
          "freshness": "fresh",
          "item_type": "decision",
          "made_at": "2026-02-06T15:00:00Z",
          "made_by": "priya_patel",
          "queue_reason": "Evidence quality assessed as 'insufficient': missing evidence links or corroboration",
          "rationale": "Governing architectural baseline decision",
          "repo": "acme-eng/distributed-cache-service",
          "repo_full_name": "acme-eng/distributed-cache-service",
          "review_status": "pending_review",
          "state": "accepted",
          "superseded_by_decision_id": null,
          "supersedes_decision_id": null,
          "title": "Architectural Decision dec_cache_redis_01"
        },
        {
          "alternatives_json": "[{\"description\": \"Redis cluster deployment\", \"rejection_reason\": \"Adds operational complexity and 1-2ms network hop over in-process memory\", \"evidence_event_ids\": [\"evt_pr_cache_38\"]}]",
          "confidence": 0.82,
          "decision_id": "dec_cache_local_lru_proposed",
          "evidence_assessment": "weak",
          "freshness": "fresh",
          "item_type": "decision",
          "made_at": "2026-02-03T14:30:00Z",
          "made_by": "marcus_vance",
          "queue_reason": "Evidence quality assessed as 'weak': single source group without independent corroboration",
          "rationale": "Keep cache strictly inside Python heap to guarantee sub-millisecond access and avoid external Redis infra.",
          "repo": "acme-eng/distributed-cache-service",
          "repo_full_name": "acme-eng/distributed-cache-service",
          "review_status": "pending_review",
          "state": "superseded",
          "superseded_by_decision_id": "dec_cache_redis_accepted",
          "supersedes_decision_id": null,
          "title": "Retain In-Memory LRU Cache with Process Memory Cap"
        },
        {
          "alternatives_json": "[{\"description\": \"Deadband on-off threshold control +/- 1.5C\", \"rejection_reason\": \"Benchmarking revealed 17% higher latency and persistent 6.2C transient overshoot\", \"evidence_event_ids\": [\"evt_rev_thermal_comm2\"]}]",
          "confidence": 0.96,
          "decision_id": "dec_thermal_deadband_rejected",
          "evidence_assessment": "weak",
          "freshness": "fresh",
          "item_type": "decision",
          "made_at": "2026-01-12T15:00:00Z",
          "made_by": "sarah_chen",
          "queue_reason": "Evidence quality assessed as 'weak': single source group without independent corroboration",
          "rationale": "Tested in simulation following Issue #12; deadband was insufficient to prevent emergency chamber thermal trip.",
          "repo": "acme-eng/thermal-control-system",
          "repo_full_name": "acme-eng/thermal-control-system",
          "review_status": "auto_confirmed",
          "state": "rejected",
          "superseded_by_decision_id": null,
          "supersedes_decision_id": null,
          "title": "Reject Simple Deadband Hysteresis for Thermal Control"
        },
        {
          "alternatives_json": "[{\"description\": \"In-memory LRU cache with soft memory cap (PR #38)\", \"rejection_reason\": \"Rejected: Local cache causes cache stampedes and memory duplication across container replicas\", \"evidence_event_ids\": [\"evt_rev_cache_c201\"]}]",
          "confidence": 0.97,
          "decision_id": "dec_cache_redis_accepted",
          "evidence_assessment": "insufficient",
          "freshness": "fresh",
          "item_type": "decision",
          "made_at": "2026-02-06T15:00:00Z",
          "made_by": "priya_patel",
          "queue_reason": "Evidence quality assessed as 'insufficient': missing evidence links or corroboration",
          "rationale": "ADR 0009: Decommission local in-memory dict and migrate to Redis cluster to prevent container OOMs and maintain cache consistency across autoscaled pods.",
          "repo": "acme-eng/distributed-cache-service",
          "repo_full_name": "acme-eng/distributed-cache-service",
          "review_status": "auto_confirmed",
          "state": "accepted",
          "superseded_by_decision_id": null,
          "supersedes_decision_id": "dec_cache_local_lru_proposed",
          "title": "Migrate from In-Memory LRU to Distributed Redis Cluster"
        },
        {
          "alternatives_json": "[{\"description\": \"On-off hysteresis deadband controller\", \"rejection_reason\": \"Caused 17% latency increase and 6.2C overshoot in thermal transient tests\", \"evidence_event_ids\": [\"evt_rev_thermal_comm2\"]}]",
          "confidence": 0.98,
          "decision_id": "dec_thermal_pid_accepted",
          "evidence_assessment": "insufficient",
          "freshness": "fresh",
          "item_type": "decision",
          "made_at": "2026-01-15T16:00:00Z",
          "made_by": "sarah_chen",
          "queue_reason": "Evidence quality assessed as 'insufficient': missing evidence links or corroboration",
          "rationale": "ADR 0004: Continuous PID loop with anti-windup clamping guarantees stability within +/- 0.4C of setpoint under heavy duty cycle.",
          "repo": "acme-eng/thermal-control-system",
          "repo_full_name": "acme-eng/thermal-control-system",
          "review_status": "auto_confirmed",
          "state": "accepted",
          "superseded_by_decision_id": null,
          "supersedes_decision_id": null,
          "title": "Adopt Discrete PID Controller for Chamber Temperature Regulation"
        },
        {
          "confidence": 0.88,
          "edge_id": "edge_conflicts_with_dec_cache_local__dec_cache_redis_",
          "from_id": "dec_cache_local_lru_proposed",
          "item_type": "conflict",
          "made_at": "2026-02-06T15:00:00Z",
          "queue_reason": "Contributor/Architectural Disagreement Detected",
          "review_status": "pending_review",
          "title": "Conflict: 'Retain In-Memory LRU Cache with Process Memory Cap' vs 'Migrate from In-Memory LRU to Distributed Redis Cluster'",
          "to_id": "dec_cache_redis_accepted"
        },
        {
          "confidence": 0.93,
          "decision_id": "dec_cache_redis_01",
          "edge_id": "edge_drift_src/cach_dec_cach",
          "entity_id": "src/cache/store.py",
          "item_type": "drift",
          "made_at": "2026-10-12T00:00:00Z",
          "queue_reason": "Code diff contradicts accepted decision 'Architectural Decision dec_cache_redis_01'",
          "review_status": "pending_review",
          "title": "Drift on artifact"
        },
        {
          "confidence": 0.93,
          "decision_id": "dec_thermal_pid_01",
          "edge_id": "edge_drift_src/ther_dec_ther",
          "entity_id": "src/thermal/control.py",
          "item_type": "drift",
          "made_at": "2026-10-12T00:00:00Z",
          "queue_reason": "Code diff contradicts accepted decision 'Architectural Decision dec_thermal_pid_01'",
          "review_status": "pending_review",
          "title": "Drift on artifact"
        }
      ],
      "status": "success"
    },
    "stats": {
      "data": {
        "conflicts": 1,
        "decisions": 7,
        "drifts": 2,
        "edges": 21,
        "entities": 9,
        "events": 9,
        "finding_feedback": {
          "confirm": 0,
          "dismiss": 0,
          "reopen": 0,
          "total": 0
        }
      },
      "status": "success"
    },
    "timeline_all": {
      "data": [
        {
          "affected_artifacts": [
            {
              "canonical_path": "src/thermal/control.py",
              "entity_type": "file"
            },
            {
              "canonical_path": "src/thermal/control.py::regulate_temperature",
              "entity_type": "function"
            }
          ],
          "alternatives_considered": [
            {
              "description": "Deadband on-off threshold control +/- 1.5C",
              "evidence_event_ids": [
                "evt_rev_thermal_comm2"
              ],
              "rejection_reason": "Benchmarking revealed 17% higher latency and persistent 6.2C transient overshoot"
            }
          ],
          "alternatives_json": "[{\"description\": \"Deadband on-off threshold control +/- 1.5C\", \"rejection_reason\": \"Benchmarking revealed 17% higher latency and persistent 6.2C transient overshoot\", \"evidence_event_ids\": [\"evt_rev_thermal_comm2\"]}]",
          "confidence": 0.96,
          "decision_id": "dec_thermal_deadband_rejected",
          "evidence_assessment": "weak",
          "evidence_count": 2,
          "freshness": "fresh",
          "made_at": "2026-01-12T15:00:00Z",
          "made_by": "sarah_chen",
          "rationale": "Tested in simulation following Issue #12; deadband was insufficient to prevent emergency chamber thermal trip.",
          "repo": "acme-eng/thermal-control-system",
          "repo_full_name": "acme-eng/thermal-control-system",
          "review_status": "auto_confirmed",
          "state": "rejected",
          "superseded_by_decision_id": null,
          "supersedes_decision_id": null,
          "title": "Reject Simple Deadband Hysteresis for Thermal Control"
        },
        {
          "affected_artifacts": [],
          "alternatives_considered": [],
          "alternatives_json": "[]",
          "confidence": 0.8,
          "decision_id": "dec_thermal_bangbang_02",
          "evidence_assessment": "insufficient",
          "evidence_count": 1,
          "freshness": "fresh",
          "made_at": "2026-01-12T15:00:00Z",
          "made_by": "sarah_chen",
          "rationale": "Governing architectural baseline decision",
          "repo": "acme-eng/thermal-control-system",
          "repo_full_name": "acme-eng/thermal-control-system",
          "review_status": "pending_review",
          "state": "rejected",
          "superseded_by_decision_id": null,
          "supersedes_decision_id": null,
          "title": "Architectural Decision dec_thermal_bangbang_02"
        },
        {
          "affected_artifacts": [
            {
              "canonical_path": "deps::scipy",
              "entity_type": "dependency"
            },
            {
              "canonical_path": "src/thermal/control.py",
              "entity_type": "file"
            },
            {
              "canonical_path": "src/thermal/control.py::regulate_temperature",
              "entity_type": "function"
            }
          ],
          "alternatives_considered": [
            {
              "description": "On-off hysteresis deadband controller",
              "evidence_event_ids": [
                "evt_rev_thermal_comm2"
              ],
              "rejection_reason": "Caused 17% latency increase and 6.2C overshoot in thermal transient tests"
            }
          ],
          "alternatives_json": "[{\"description\": \"On-off hysteresis deadband controller\", \"rejection_reason\": \"Caused 17% latency increase and 6.2C overshoot in thermal transient tests\", \"evidence_event_ids\": [\"evt_rev_thermal_comm2\"]}]",
          "confidence": 0.98,
          "decision_id": "dec_thermal_pid_accepted",
          "evidence_assessment": "insufficient",
          "evidence_count": 2,
          "freshness": "fresh",
          "made_at": "2026-01-15T16:00:00Z",
          "made_by": "sarah_chen",
          "rationale": "ADR 0004: Continuous PID loop with anti-windup clamping guarantees stability within +/- 0.4C of setpoint under heavy duty cycle.",
          "repo": "acme-eng/thermal-control-system",
          "repo_full_name": "acme-eng/thermal-control-system",
          "review_status": "auto_confirmed",
          "state": "accepted",
          "superseded_by_decision_id": null,
          "supersedes_decision_id": null,
          "title": "Adopt Discrete PID Controller for Chamber Temperature Regulation"
        },
        {
          "affected_artifacts": [],
          "alternatives_considered": [],
          "alternatives_json": "[]",
          "confidence": 0.8,
          "decision_id": "dec_thermal_pid_01",
          "evidence_assessment": "insufficient",
          "evidence_count": 1,
          "freshness": "fresh",
          "made_at": "2026-01-15T16:00:00Z",
          "made_by": "sarah_chen",
          "rationale": "Governing architectural baseline decision",
          "repo": "acme-eng/thermal-control-system",
          "repo_full_name": "acme-eng/thermal-control-system",
          "review_status": "pending_review",
          "state": "accepted",
          "superseded_by_decision_id": null,
          "supersedes_decision_id": null,
          "title": "Architectural Decision dec_thermal_pid_01"
        },
        {
          "affected_artifacts": [
            {
              "canonical_path": "src/cache/store.py",
              "entity_type": "file"
            },
            {
              "canonical_path": "src/cache/store.py::cache_get",
              "entity_type": "function"
            },
            {
              "canonical_path": "src/cache/store.py::cache_set",
              "entity_type": "function"
            }
          ],
          "alternatives_considered": [
            {
              "description": "Redis cluster deployment",
              "evidence_event_ids": [
                "evt_pr_cache_38"
              ],
              "rejection_reason": "Adds operational complexity and 1-2ms network hop over in-process memory"
            }
          ],
          "alternatives_json": "[{\"description\": \"Redis cluster deployment\", \"rejection_reason\": \"Adds operational complexity and 1-2ms network hop over in-process memory\", \"evidence_event_ids\": [\"evt_pr_cache_38\"]}]",
          "confidence": 0.82,
          "decision_id": "dec_cache_local_lru_proposed",
          "evidence_assessment": "weak",
          "evidence_count": 1,
          "freshness": "fresh",
          "made_at": "2026-02-03T14:30:00Z",
          "made_by": "marcus_vance",
          "rationale": "Keep cache strictly inside Python heap to guarantee sub-millisecond access and avoid external Redis infra.",
          "repo": "acme-eng/distributed-cache-service",
          "repo_full_name": "acme-eng/distributed-cache-service",
          "review_status": "pending_review",
          "state": "superseded",
          "superseded_by_decision_id": "dec_cache_redis_accepted",
          "supersedes_decision_id": null,
          "title": "Retain In-Memory LRU Cache with Process Memory Cap"
        },
        {
          "affected_artifacts": [
            {
              "canonical_path": "deps::redis",
              "entity_type": "dependency"
            },
            {
              "canonical_path": "src/cache/store.py",
              "entity_type": "file"
            },
            {
              "canonical_path": "src/cache/store.py::cache_get",
              "entity_type": "function"
            },
            {
              "canonical_path": "src/cache/store.py::cache_set",
              "entity_type": "function"
            }
          ],
          "alternatives_considered": [
            {
              "description": "In-memory LRU cache with soft memory cap (PR #38)",
              "evidence_event_ids": [
                "evt_rev_cache_c201"
              ],
              "rejection_reason": "Rejected: Local cache causes cache stampedes and memory duplication across container replicas"
            }
          ],
          "alternatives_json": "[{\"description\": \"In-memory LRU cache with soft memory cap (PR #38)\", \"rejection_reason\": \"Rejected: Local cache causes cache stampedes and memory duplication across container replicas\", \"evidence_event_ids\": [\"evt_rev_cache_c201\"]}]",
          "confidence": 0.97,
          "decision_id": "dec_cache_redis_accepted",
          "evidence_assessment": "insufficient",
          "evidence_count": 2,
          "freshness": "fresh",
          "made_at": "2026-02-06T15:00:00Z",
          "made_by": "priya_patel",
          "rationale": "ADR 0009: Decommission local in-memory dict and migrate to Redis cluster to prevent container OOMs and maintain cache consistency across autoscaled pods.",
          "repo": "acme-eng/distributed-cache-service",
          "repo_full_name": "acme-eng/distributed-cache-service",
          "review_status": "auto_confirmed",
          "state": "accepted",
          "superseded_by_decision_id": null,
          "supersedes_decision_id": "dec_cache_local_lru_proposed",
          "title": "Migrate from In-Memory LRU to Distributed Redis Cluster"
        },
        {
          "affected_artifacts": [],
          "alternatives_considered": [],
          "alternatives_json": "[]",
          "confidence": 0.8,
          "decision_id": "dec_cache_redis_01",
          "evidence_assessment": "insufficient",
          "evidence_count": 1,
          "freshness": "fresh",
          "made_at": "2026-02-06T15:00:00Z",
          "made_by": "priya_patel",
          "rationale": "Governing architectural baseline decision",
          "repo": "acme-eng/distributed-cache-service",
          "repo_full_name": "acme-eng/distributed-cache-service",
          "review_status": "pending_review",
          "state": "accepted",
          "superseded_by_decision_id": null,
          "supersedes_decision_id": null,
          "title": "Architectural Decision dec_cache_redis_01"
        }
      ],
      "status": "success"
    },
    "timeline_cache": {
      "data": [
        {
          "affected_artifacts": [
            {
              "canonical_path": "src/cache/store.py",
              "entity_type": "file"
            },
            {
              "canonical_path": "src/cache/store.py::cache_get",
              "entity_type": "function"
            },
            {
              "canonical_path": "src/cache/store.py::cache_set",
              "entity_type": "function"
            }
          ],
          "alternatives_considered": [
            {
              "description": "Redis cluster deployment",
              "evidence_event_ids": [
                "evt_pr_cache_38"
              ],
              "rejection_reason": "Adds operational complexity and 1-2ms network hop over in-process memory"
            }
          ],
          "alternatives_json": "[{\"description\": \"Redis cluster deployment\", \"rejection_reason\": \"Adds operational complexity and 1-2ms network hop over in-process memory\", \"evidence_event_ids\": [\"evt_pr_cache_38\"]}]",
          "confidence": 0.82,
          "decision_id": "dec_cache_local_lru_proposed",
          "evidence_assessment": "weak",
          "evidence_count": 1,
          "freshness": "fresh",
          "made_at": "2026-02-03T14:30:00Z",
          "made_by": "marcus_vance",
          "rationale": "Keep cache strictly inside Python heap to guarantee sub-millisecond access and avoid external Redis infra.",
          "repo": "acme-eng/distributed-cache-service",
          "repo_full_name": "acme-eng/distributed-cache-service",
          "review_status": "pending_review",
          "state": "superseded",
          "superseded_by_decision_id": "dec_cache_redis_accepted",
          "supersedes_decision_id": null,
          "title": "Retain In-Memory LRU Cache with Process Memory Cap"
        },
        {
          "affected_artifacts": [
            {
              "canonical_path": "deps::redis",
              "entity_type": "dependency"
            },
            {
              "canonical_path": "src/cache/store.py",
              "entity_type": "file"
            },
            {
              "canonical_path": "src/cache/store.py::cache_get",
              "entity_type": "function"
            },
            {
              "canonical_path": "src/cache/store.py::cache_set",
              "entity_type": "function"
            }
          ],
          "alternatives_considered": [
            {
              "description": "In-memory LRU cache with soft memory cap (PR #38)",
              "evidence_event_ids": [
                "evt_rev_cache_c201"
              ],
              "rejection_reason": "Rejected: Local cache causes cache stampedes and memory duplication across container replicas"
            }
          ],
          "alternatives_json": "[{\"description\": \"In-memory LRU cache with soft memory cap (PR #38)\", \"rejection_reason\": \"Rejected: Local cache causes cache stampedes and memory duplication across container replicas\", \"evidence_event_ids\": [\"evt_rev_cache_c201\"]}]",
          "confidence": 0.97,
          "decision_id": "dec_cache_redis_accepted",
          "evidence_assessment": "insufficient",
          "evidence_count": 2,
          "freshness": "fresh",
          "made_at": "2026-02-06T15:00:00Z",
          "made_by": "priya_patel",
          "rationale": "ADR 0009: Decommission local in-memory dict and migrate to Redis cluster to prevent container OOMs and maintain cache consistency across autoscaled pods.",
          "repo": "acme-eng/distributed-cache-service",
          "repo_full_name": "acme-eng/distributed-cache-service",
          "review_status": "auto_confirmed",
          "state": "accepted",
          "superseded_by_decision_id": null,
          "supersedes_decision_id": "dec_cache_local_lru_proposed",
          "title": "Migrate from In-Memory LRU to Distributed Redis Cluster"
        },
        {
          "affected_artifacts": [],
          "alternatives_considered": [],
          "alternatives_json": "[]",
          "confidence": 0.8,
          "decision_id": "dec_cache_redis_01",
          "evidence_assessment": "insufficient",
          "evidence_count": 1,
          "freshness": "fresh",
          "made_at": "2026-02-06T15:00:00Z",
          "made_by": "priya_patel",
          "rationale": "Governing architectural baseline decision",
          "repo": "acme-eng/distributed-cache-service",
          "repo_full_name": "acme-eng/distributed-cache-service",
          "review_status": "pending_review",
          "state": "accepted",
          "superseded_by_decision_id": null,
          "supersedes_decision_id": null,
          "title": "Architectural Decision dec_cache_redis_01"
        }
      ],
      "status": "success"
    },
    "timeline_thermal": {
      "data": [
        {
          "affected_artifacts": [
            {
              "canonical_path": "src/thermal/control.py",
              "entity_type": "file"
            },
            {
              "canonical_path": "src/thermal/control.py::regulate_temperature",
              "entity_type": "function"
            }
          ],
          "alternatives_considered": [
            {
              "description": "Deadband on-off threshold control +/- 1.5C",
              "evidence_event_ids": [
                "evt_rev_thermal_comm2"
              ],
              "rejection_reason": "Benchmarking revealed 17% higher latency and persistent 6.2C transient overshoot"
            }
          ],
          "alternatives_json": "[{\"description\": \"Deadband on-off threshold control +/- 1.5C\", \"rejection_reason\": \"Benchmarking revealed 17% higher latency and persistent 6.2C transient overshoot\", \"evidence_event_ids\": [\"evt_rev_thermal_comm2\"]}]",
          "confidence": 0.96,
          "decision_id": "dec_thermal_deadband_rejected",
          "evidence_assessment": "weak",
          "evidence_count": 2,
          "freshness": "fresh",
          "made_at": "2026-01-12T15:00:00Z",
          "made_by": "sarah_chen",
          "rationale": "Tested in simulation following Issue #12; deadband was insufficient to prevent emergency chamber thermal trip.",
          "repo": "acme-eng/thermal-control-system",
          "repo_full_name": "acme-eng/thermal-control-system",
          "review_status": "auto_confirmed",
          "state": "rejected",
          "superseded_by_decision_id": null,
          "supersedes_decision_id": null,
          "title": "Reject Simple Deadband Hysteresis for Thermal Control"
        },
        {
          "affected_artifacts": [],
          "alternatives_considered": [],
          "alternatives_json": "[]",
          "confidence": 0.8,
          "decision_id": "dec_thermal_bangbang_02",
          "evidence_assessment": "insufficient",
          "evidence_count": 1,
          "freshness": "fresh",
          "made_at": "2026-01-12T15:00:00Z",
          "made_by": "sarah_chen",
          "rationale": "Governing architectural baseline decision",
          "repo": "acme-eng/thermal-control-system",
          "repo_full_name": "acme-eng/thermal-control-system",
          "review_status": "pending_review",
          "state": "rejected",
          "superseded_by_decision_id": null,
          "supersedes_decision_id": null,
          "title": "Architectural Decision dec_thermal_bangbang_02"
        },
        {
          "affected_artifacts": [
            {
              "canonical_path": "deps::scipy",
              "entity_type": "dependency"
            },
            {
              "canonical_path": "src/thermal/control.py",
              "entity_type": "file"
            },
            {
              "canonical_path": "src/thermal/control.py::regulate_temperature",
              "entity_type": "function"
            }
          ],
          "alternatives_considered": [
            {
              "description": "On-off hysteresis deadband controller",
              "evidence_event_ids": [
                "evt_rev_thermal_comm2"
              ],
              "rejection_reason": "Caused 17% latency increase and 6.2C overshoot in thermal transient tests"
            }
          ],
          "alternatives_json": "[{\"description\": \"On-off hysteresis deadband controller\", \"rejection_reason\": \"Caused 17% latency increase and 6.2C overshoot in thermal transient tests\", \"evidence_event_ids\": [\"evt_rev_thermal_comm2\"]}]",
          "confidence": 0.98,
          "decision_id": "dec_thermal_pid_accepted",
          "evidence_assessment": "insufficient",
          "evidence_count": 2,
          "freshness": "fresh",
          "made_at": "2026-01-15T16:00:00Z",
          "made_by": "sarah_chen",
          "rationale": "ADR 0004: Continuous PID loop with anti-windup clamping guarantees stability within +/- 0.4C of setpoint under heavy duty cycle.",
          "repo": "acme-eng/thermal-control-system",
          "repo_full_name": "acme-eng/thermal-control-system",
          "review_status": "auto_confirmed",
          "state": "accepted",
          "superseded_by_decision_id": null,
          "supersedes_decision_id": null,
          "title": "Adopt Discrete PID Controller for Chamber Temperature Regulation"
        },
        {
          "affected_artifacts": [],
          "alternatives_considered": [],
          "alternatives_json": "[]",
          "confidence": 0.8,
          "decision_id": "dec_thermal_pid_01",
          "evidence_assessment": "insufficient",
          "evidence_count": 1,
          "freshness": "fresh",
          "made_at": "2026-01-15T16:00:00Z",
          "made_by": "sarah_chen",
          "rationale": "Governing architectural baseline decision",
          "repo": "acme-eng/thermal-control-system",
          "repo_full_name": "acme-eng/thermal-control-system",
          "review_status": "pending_review",
          "state": "accepted",
          "superseded_by_decision_id": null,
          "supersedes_decision_id": null,
          "title": "Architectural Decision dec_thermal_pid_01"
        }
      ],
      "status": "success"
    }
  },
  "evidences": {
    "dec_cache_local_lru_proposed": {
      "data": {
        "conflicting_evidence": [
          {
            "decision_id": "dec_cache_redis_accepted",
            "made_at": "2026-02-06T15:00:00Z",
            "state": "accepted",
            "title": "Migrate from In-Memory LRU to Distributed Redis Cluster",
            "type": "related_decision_on_entity"
          }
        ],
        "decision": {
          "alternatives_considered": [
            {
              "description": "Redis cluster deployment",
              "evidence_event_ids": [
                "evt_pr_cache_38"
              ],
              "rejection_reason": "Adds operational complexity and 1-2ms network hop over in-process memory"
            }
          ],
          "alternatives_json": "[{\"description\": \"Redis cluster deployment\", \"rejection_reason\": \"Adds operational complexity and 1-2ms network hop over in-process memory\", \"evidence_event_ids\": [\"evt_pr_cache_38\"]}]",
          "confidence": 0.82,
          "decision_id": "dec_cache_local_lru_proposed",
          "evidence_assessment": "weak",
          "freshness": "fresh",
          "made_at": "2026-02-03T14:30:00Z",
          "made_by": "marcus_vance",
          "rationale": "Keep cache strictly inside Python heap to guarantee sub-millisecond access and avoid external Redis infra.",
          "repo": "acme-eng/distributed-cache-service",
          "repo_full_name": "acme-eng/distributed-cache-service",
          "review_status": "pending_review",
          "state": "superseded",
          "superseded_by_decision_id": "dec_cache_redis_accepted",
          "supersedes_decision_id": null,
          "title": "Retain In-Memory LRU Cache with Process Memory Cap"
        },
        "direct_support": [
          {
            "author": "marcus_vance",
            "date": "2026-02-03T14:30:00Z",
            "event_id": "evt_pr_cache_38",
            "passage_end": 203,
            "passage_start": 155,
            "relation": "direct",
            "relevant_passage": "Keeps caching local with sub-millisecond access.",
            "source_group": "thread:acme-eng/distributed-cache-service#38",
            "source_link": "https://github.com/acme-eng/distributed-cache-service/pull/38",
            "source_type": "github_pr",
            "title": "PR #38: Add soft memory cap to in-memory LRU cache (Closes #34)",
            "url_format_ok": true
          }
        ],
        "discussion_events": [],
        "evidence_assessment": {
          "label": "weak"
        },
        "evidence_events": [
          {
            "artifacts_touched": [
              "src/cache/store.py"
            ],
            "author": "marcus_vance",
            "body": "Adds a maximum memory threshold to local Python process memory before aggressive eviction. Keeps caching local with sub-millisecond access.",
            "event_id": "evt_pr_cache_38",
            "parent_event_ids": [
              "evt_issue_cache_34"
            ],
            "raw_metadata": {},
            "repo": "acme-eng/distributed-cache-service",
            "repo_full_name": "acme-eng/distributed-cache-service",
            "source_id": "38",
            "source_type": "github_pr",
            "source_url": "https://github.com/acme-eng/distributed-cache-service/pull/38",
            "title": "PR #38: Add soft memory cap to in-memory LRU cache (Closes #34)",
            "ts": "2026-02-03T14:30:00Z"
          }
        ],
        "indirect_support": [
          {
            "author": "marcus_vance",
            "date": "2026-02-03T14:30:00Z",
            "event_id": "evt_pr_cache_38",
            "passage_end": null,
            "passage_start": null,
            "relation": "indirect",
            "relevant_passage": null,
            "source_group": "thread:acme-eng/distributed-cache-service#38",
            "source_link": "https://github.com/acme-eng/distributed-cache-service/pull/38",
            "source_type": "github_pr",
            "title": "PR #38: Add soft memory cap to in-memory LRU cache (Closes #34)",
            "url_format_ok": true
          }
        ],
        "lifecycle_state": "superseded",
        "missing_corroboration": [
          "no independent corroborating source recorded (single source group)",
          "no outcome/test evidence linked"
        ],
        "needs_review": true,
        "state_history": [
          {
            "changed_at": "2026-02-03T14:30:00Z",
            "changed_by": "marcus_vance",
            "decision_id": "dec_cache_local_lru_proposed",
            "from_state": null,
            "history_id": "hist_init_dec_cache_local_lru_proposed_1792750872740746600_8e968e",
            "notes": "Initial state: proposed. Reason: Keep cache strictly inside Python heap to guarantee sub-millisecond access and avoid external Redis infra.",
            "reconstructed": 0,
            "repo_full_name": "acme-eng/distributed-cache-service",
            "state": "proposed"
          },
          {
            "changed_at": "2026-02-04T10:00:00Z",
            "changed_by": "marcus_vance",
            "decision_id": "dec_cache_local_lru_proposed",
            "from_state": "proposed",
            "history_id": "hist_dec_cache_local_lru_proposed_1792750872808808300_1f8d83",
            "notes": "Transition: proposed -> accepted. Reason: Accepted temporary in-memory LRU cache with soft memory cap",
            "reconstructed": 0,
            "repo_full_name": "acme-eng/distributed-cache-service",
            "state": "accepted"
          },
          {
            "changed_at": "2026-02-06T15:00:00Z",
            "changed_by": "priya_patel",
            "decision_id": "dec_cache_local_lru_proposed",
            "from_state": "accepted",
            "history_id": "hist_dec_cache_local_lru_proposed_1792750872992070200_856b6a",
            "notes": "Transition: accepted -> superseded. Reason: ADR 0009: Migrated from in-memory cache to distributed Redis cluster",
            "reconstructed": 0,
            "repo_full_name": "acme-eng/distributed-cache-service",
            "state": "superseded"
          }
        ]
      },
      "status": "success"
    },
    "dec_cache_redis_01": {
      "data": {
        "conflicting_evidence": [],
        "decision": {
          "alternatives_considered": [],
          "alternatives_json": "[]",
          "confidence": 0.8,
          "decision_id": "dec_cache_redis_01",
          "evidence_assessment": "insufficient",
          "freshness": "fresh",
          "made_at": "2026-02-06T15:00:00Z",
          "made_by": "priya_patel",
          "rationale": "Governing architectural baseline decision",
          "repo": "acme-eng/distributed-cache-service",
          "repo_full_name": "acme-eng/distributed-cache-service",
          "review_status": "pending_review",
          "state": "accepted",
          "superseded_by_decision_id": null,
          "supersedes_decision_id": null,
          "title": "Architectural Decision dec_cache_redis_01"
        },
        "direct_support": [
          {
            "author": "priya_patel",
            "date": "2026-02-06T15:00:00Z",
            "event_id": "evt_adr_cache_0009",
            "passage_end": 293,
            "passage_start": 284,
            "relation": "direct",
            "relevant_passage": "Decision:",
            "source_group": "doc:acme-eng/distributed-cache-service:docs/adr/0009-redis-cluster-cache.md",
            "source_link": "https://github.com/acme-eng/distributed-cache-service/blob/main/docs/adr/0009-redis-cluster-cache.md",
            "source_type": "adr",
            "title": "ADR 0009: Migrate to Redis Cluster for Distributed Caching",
            "url_format_ok": true
          }
        ],
        "discussion_events": [],
        "evidence_assessment": {
          "label": "weak"
        },
        "evidence_events": [
          {
            "artifacts_touched": [
              "src/cache/store.py",
              "docs/adr/0009-redis-cluster-cache.md"
            ],
            "author": "priya_patel",
            "body": "Status: accepted\n\nContext:\nIn-memory LRU caching caused node OOM crashes (#34) and replica cache incoherence. PR #38 attempted local memory capping but was rejected because container autoscaling requires shared cache state.\n\nDecision:\nDecommission in-memory LRU dict in store.py and implement Redis cluster client with sentinel failover and connection pooling.\n\nConsequences:\n- Resilient distributed cache state across all container instances.\n- Solves memory leak and OOM termination.\n- Network overhead ~1.2ms per roundtrip.",
            "event_id": "evt_adr_cache_0009",
            "parent_event_ids": [],
            "raw_metadata": {
              "parsed_adr": {
                "consequences": "Resilient cache state across all pods; solves OOM crashes.",
                "context": "Local in-memory cache caused OOM crashes. Local memory capping cannot sync across pods.",
                "decision": "Decommission in-memory cache and migrate to Redis cluster.",
                "status": "accepted",
                "title": "Migrate to Redis Cluster for Distributed Caching"
              }
            },
            "repo": "acme-eng/distributed-cache-service",
            "repo_full_name": "acme-eng/distributed-cache-service",
            "source_id": "docs/adr/0009-redis-cluster-cache.md",
            "source_type": "adr",
            "source_url": "https://github.com/acme-eng/distributed-cache-service/blob/main/docs/adr/0009-redis-cluster-cache.md",
            "title": "ADR 0009: Migrate to Redis Cluster for Distributed Caching",
            "ts": "2026-02-06T15:00:00Z"
          }
        ],
        "indirect_support": [],
        "lifecycle_state": "accepted",
        "missing_corroboration": [
          "no independent source besides the ADR",
          "no outcome/test evidence linked"
        ],
        "needs_review": true,
        "state_history": [
          {
            "changed_at": "2026-02-06T15:00:00Z",
            "changed_by": "priya_patel",
            "decision_id": "dec_cache_redis_01",
            "from_state": null,
            "history_id": "hist_init_dec_cache_redis_01_1792750873160090100_412680",
            "notes": "Initial state: accepted. Reason: Governing architectural baseline decision",
            "reconstructed": 0,
            "repo_full_name": "acme-eng/distributed-cache-service",
            "state": "accepted"
          }
        ]
      },
      "status": "success"
    },
    "dec_cache_redis_accepted": {
      "data": {
        "conflicting_evidence": [
          {
            "event_id": "evt_rev_cache_c201",
            "passage_text": "Priya review on PR #38: In-memory cache cannot scale across replicas",
            "relation": "contradicting",
            "source_group": "thread:acme-eng/distributed-cache-service#38",
            "type": "contradicting_passage"
          },
          {
            "decision_id": "dec_cache_local_lru_proposed",
            "made_at": "2026-02-03T14:30:00Z",
            "state": "superseded",
            "title": "Retain In-Memory LRU Cache with Process Memory Cap",
            "type": "related_decision_on_entity"
          }
        ],
        "decision": {
          "alternatives_considered": [
            {
              "description": "In-memory LRU cache with soft memory cap (PR #38)",
              "evidence_event_ids": [
                "evt_rev_cache_c201"
              ],
              "rejection_reason": "Rejected: Local cache causes cache stampedes and memory duplication across container replicas"
            }
          ],
          "alternatives_json": "[{\"description\": \"In-memory LRU cache with soft memory cap (PR #38)\", \"rejection_reason\": \"Rejected: Local cache causes cache stampedes and memory duplication across container replicas\", \"evidence_event_ids\": [\"evt_rev_cache_c201\"]}]",
          "confidence": 0.97,
          "decision_id": "dec_cache_redis_accepted",
          "evidence_assessment": "insufficient",
          "freshness": "fresh",
          "made_at": "2026-02-06T15:00:00Z",
          "made_by": "priya_patel",
          "rationale": "ADR 0009: Decommission local in-memory dict and migrate to Redis cluster to prevent container OOMs and maintain cache consistency across autoscaled pods.",
          "repo": "acme-eng/distributed-cache-service",
          "repo_full_name": "acme-eng/distributed-cache-service",
          "review_status": "auto_confirmed",
          "state": "accepted",
          "superseded_by_decision_id": null,
          "supersedes_decision_id": "dec_cache_local_lru_proposed",
          "title": "Migrate from In-Memory LRU to Distributed Redis Cluster"
        },
        "direct_support": [
          {
            "author": "priya_patel",
            "date": "2026-02-06T15:00:00Z",
            "event_id": "evt_adr_cache_0009",
            "passage_end": 282,
            "passage_start": 169,
            "relation": "direct",
            "relevant_passage": "PR #38 attempted local memory capping but was rejected because container autoscaling requires shared cache state.",
            "source_group": "doc:acme-eng/distributed-cache-service:docs/adr/0009-redis-cluster-cache.md",
            "source_link": "https://github.com/acme-eng/distributed-cache-service/blob/main/docs/adr/0009-redis-cluster-cache.md",
            "source_type": "adr",
            "title": "ADR 0009: Migrate to Redis Cluster for Distributed Caching",
            "url_format_ok": true
          },
          {
            "author": "priya_patel",
            "date": "2026-02-06T15:00:00Z",
            "event_id": "evt_adr_cache_0009",
            "passage_end": 58,
            "passage_start": 0,
            "relation": "direct",
            "relevant_passage": "ADR 0009: Migrate to Redis Cluster for Distributed Caching",
            "source_group": "doc:acme-eng/distributed-cache-service:docs/adr/0009-redis-cluster-cache.md",
            "source_link": "https://github.com/acme-eng/distributed-cache-service/blob/main/docs/adr/0009-redis-cluster-cache.md",
            "source_type": "adr",
            "title": "ADR 0009: Migrate to Redis Cluster for Distributed Caching",
            "url_format_ok": true
          },
          {
            "author": "priya_patel",
            "date": "2026-02-04T09:00:00Z",
            "event_id": "evt_rev_cache_c201",
            "passage_end": 220,
            "passage_start": 184,
            "relation": "direct",
            "relevant_passage": "We need a distributed Redis cluster.",
            "source_group": "thread:acme-eng/distributed-cache-service#38",
            "source_link": "https://github.com/acme-eng/distributed-cache-service/pull/38#discussion_r201",
            "source_type": "pr_review_comment",
            "title": "Priya review on PR #38: In-memory cache cannot scale across replicas",
            "url_format_ok": true
          }
        ],
        "discussion_events": [],
        "evidence_assessment": {
          "label": "contradicted"
        },
        "evidence_events": [
          {
            "artifacts_touched": [
              "src/cache/store.py"
            ],
            "author": "priya_patel",
            "body": "Local LRU will never solve cache stampedes across multiple container replicas. Each pod will maintain cold caches. We need a distributed Redis cluster.",
            "event_id": "evt_rev_cache_c201",
            "parent_event_ids": [
              "evt_pr_cache_38"
            ],
            "raw_metadata": {},
            "repo": "acme-eng/distributed-cache-service",
            "repo_full_name": "acme-eng/distributed-cache-service",
            "source_id": "c201",
            "source_type": "pr_review_comment",
            "source_url": "https://github.com/acme-eng/distributed-cache-service/pull/38#discussion_r201",
            "title": "Priya review on PR #38: In-memory cache cannot scale across replicas",
            "ts": "2026-02-04T09:00:00Z"
          },
          {
            "artifacts_touched": [
              "src/cache/store.py",
              "docs/adr/0009-redis-cluster-cache.md"
            ],
            "author": "priya_patel",
            "body": "Status: accepted\n\nContext:\nIn-memory LRU caching caused node OOM crashes (#34) and replica cache incoherence. PR #38 attempted local memory capping but was rejected because container autoscaling requires shared cache state.\n\nDecision:\nDecommission in-memory LRU dict in store.py and implement Redis cluster client with sentinel failover and connection pooling.\n\nConsequences:\n- Resilient distributed cache state across all container instances.\n- Solves memory leak and OOM termination.\n- Network overhead ~1.2ms per roundtrip.",
            "event_id": "evt_adr_cache_0009",
            "parent_event_ids": [],
            "raw_metadata": {
              "parsed_adr": {
                "consequences": "Resilient cache state across all pods; solves OOM crashes.",
                "context": "Local in-memory cache caused OOM crashes. Local memory capping cannot sync across pods.",
                "decision": "Decommission in-memory cache and migrate to Redis cluster.",
                "status": "accepted",
                "title": "Migrate to Redis Cluster for Distributed Caching"
              }
            },
            "repo": "acme-eng/distributed-cache-service",
            "repo_full_name": "acme-eng/distributed-cache-service",
            "source_id": "docs/adr/0009-redis-cluster-cache.md",
            "source_type": "adr",
            "source_url": "https://github.com/acme-eng/distributed-cache-service/blob/main/docs/adr/0009-redis-cluster-cache.md",
            "title": "ADR 0009: Migrate to Redis Cluster for Distributed Caching",
            "ts": "2026-02-06T15:00:00Z"
          }
        ],
        "indirect_support": [],
        "lifecycle_state": "accepted",
        "missing_corroboration": [
          "no outcome/test evidence linked"
        ],
        "needs_review": true,
        "state_history": [
          {
            "changed_at": "2026-02-06T15:00:00Z",
            "changed_by": "priya_patel",
            "decision_id": "dec_cache_redis_accepted",
            "from_state": null,
            "history_id": "hist_init_dec_cache_redis_accepted_1792750872836810900_259752",
            "notes": "Initial state: accepted. Reason: ADR 0009: Decommission local in-memory dict and migrate to Redis cluster to prevent container OOMs and maintain cache consistency across autoscaled pods.",
            "reconstructed": 0,
            "repo_full_name": "acme-eng/distributed-cache-service",
            "state": "accepted"
          }
        ]
      },
      "status": "success"
    },
    "dec_thermal_bangbang_02": {
      "data": {
        "conflicting_evidence": [],
        "decision": {
          "alternatives_considered": [],
          "alternatives_json": "[]",
          "confidence": 0.8,
          "decision_id": "dec_thermal_bangbang_02",
          "evidence_assessment": "insufficient",
          "freshness": "fresh",
          "made_at": "2026-01-12T15:00:00Z",
          "made_by": "sarah_chen",
          "rationale": "Governing architectural baseline decision",
          "repo": "acme-eng/thermal-control-system",
          "repo_full_name": "acme-eng/thermal-control-system",
          "review_status": "pending_review",
          "state": "rejected",
          "superseded_by_decision_id": null,
          "supersedes_decision_id": null,
          "title": "Architectural Decision dec_thermal_bangbang_02"
        },
        "direct_support": [],
        "discussion_events": [],
        "evidence_assessment": {
          "label": "insufficient"
        },
        "evidence_events": [
          {
            "artifacts_touched": [
              "src/thermal/control.py"
            ],
            "author": "sarah_chen",
            "body": "I benchmarked deadband tuning in simulation. It increased latency by 17% and still caused a 6.2C overshoot on rapid thermal transient. We must reject on-off hysteresis and move to continuous PID control.",
            "event_id": "evt_rev_thermal_comm2",
            "parent_event_ids": [
              "evt_issue_thermal_12"
            ],
            "raw_metadata": {},
            "repo": "acme-eng/thermal-control-system",
            "repo_full_name": "acme-eng/thermal-control-system",
            "source_id": "c102",
            "source_type": "pr_review_comment",
            "source_url": "https://github.com/acme-eng/thermal-control-system/issues/12#issuecomment-102",
            "title": "Sarah on Issue #12: Benchmark results against deadband tuning",
            "ts": "2026-01-12T14:45:00Z"
          }
        ],
        "indirect_support": [
          {
            "author": "sarah_chen",
            "date": "2026-01-12T14:45:00Z",
            "event_id": "evt_rev_thermal_comm2",
            "passage_end": null,
            "passage_start": null,
            "relation": "indirect",
            "relevant_passage": null,
            "source_group": "thread:acme-eng/thermal-control-system#12",
            "source_link": "https://github.com/acme-eng/thermal-control-system/issues/12#issuecomment-102",
            "source_type": "pr_review_comment",
            "title": "Sarah on Issue #12: Benchmark results against deadband tuning",
            "url_format_ok": true
          }
        ],
        "lifecycle_state": "rejected",
        "missing_corroboration": [
          "no independent corroborating source recorded (single source group)",
          "no direct passage evidence supporting claims (indirect only)",
          "no outcome/test evidence linked"
        ],
        "needs_review": true,
        "state_history": [
          {
            "changed_at": "2026-01-12T15:00:00Z",
            "changed_by": "sarah_chen",
            "decision_id": "dec_thermal_bangbang_02",
            "from_state": null,
            "history_id": "hist_init_dec_thermal_bangbang_02_1792750873130470100_285200",
            "notes": "Initial state: rejected. Reason: Governing architectural baseline decision",
            "reconstructed": 0,
            "repo_full_name": "acme-eng/thermal-control-system",
            "state": "rejected"
          }
        ]
      },
      "status": "success"
    },
    "dec_thermal_deadband_rejected": {
      "data": {
        "conflicting_evidence": [
          {
            "decision_id": "dec_thermal_pid_accepted",
            "made_at": "2026-01-15T16:00:00Z",
            "state": "accepted",
            "title": "Adopt Discrete PID Controller for Chamber Temperature Regulation",
            "type": "related_decision_on_entity"
          }
        ],
        "decision": {
          "alternatives_considered": [
            {
              "description": "Deadband on-off threshold control +/- 1.5C",
              "evidence_event_ids": [
                "evt_rev_thermal_comm2"
              ],
              "rejection_reason": "Benchmarking revealed 17% higher latency and persistent 6.2C transient overshoot"
            }
          ],
          "alternatives_json": "[{\"description\": \"Deadband on-off threshold control +/- 1.5C\", \"rejection_reason\": \"Benchmarking revealed 17% higher latency and persistent 6.2C transient overshoot\", \"evidence_event_ids\": [\"evt_rev_thermal_comm2\"]}]",
          "confidence": 0.96,
          "decision_id": "dec_thermal_deadband_rejected",
          "evidence_assessment": "weak",
          "freshness": "fresh",
          "made_at": "2026-01-12T15:00:00Z",
          "made_by": "sarah_chen",
          "rationale": "Tested in simulation following Issue #12; deadband was insufficient to prevent emergency chamber thermal trip.",
          "repo": "acme-eng/thermal-control-system",
          "repo_full_name": "acme-eng/thermal-control-system",
          "review_status": "auto_confirmed",
          "state": "rejected",
          "superseded_by_decision_id": null,
          "supersedes_decision_id": null,
          "title": "Reject Simple Deadband Hysteresis for Thermal Control"
        },
        "direct_support": [
          {
            "author": "marcus_vance",
            "date": "2026-01-11T11:20:00Z",
            "event_id": "evt_rev_thermal_comm1",
            "passage_end": 130,
            "passage_start": 127,
            "relation": "direct",
            "relevant_passage": "5C.",
            "source_group": "thread:acme-eng/thermal-control-system#12",
            "source_link": "https://github.com/acme-eng/thermal-control-system/issues/12#issuecomment-101",
            "source_type": "pr_review_comment",
            "title": "Marcus on Issue #12: Proposed deadband tuning",
            "url_format_ok": true
          },
          {
            "author": "sarah_chen",
            "date": "2026-01-12T14:45:00Z",
            "event_id": "evt_rev_thermal_comm2",
            "passage_end": 196,
            "passage_start": 156,
            "relation": "direct",
            "relevant_passage": "2C overshoot on rapid thermal transient.",
            "source_group": "thread:acme-eng/thermal-control-system#12",
            "source_link": "https://github.com/acme-eng/thermal-control-system/issues/12#issuecomment-102",
            "source_type": "pr_review_comment",
            "title": "Sarah on Issue #12: Benchmark results against deadband tuning",
            "url_format_ok": true
          },
          {
            "author": "marcus_vance",
            "date": "2026-01-11T11:20:00Z",
            "event_id": "evt_rev_thermal_comm1",
            "passage_end": 45,
            "passage_start": 0,
            "relation": "direct",
            "relevant_passage": "Marcus on Issue #12: Proposed deadband tuning",
            "source_group": "thread:acme-eng/thermal-control-system#12",
            "source_link": "https://github.com/acme-eng/thermal-control-system/issues/12#issuecomment-101",
            "source_type": "pr_review_comment",
            "title": "Marcus on Issue #12: Proposed deadband tuning",
            "url_format_ok": true
          },
          {
            "author": "sarah_chen",
            "date": "2026-01-12T14:45:00Z",
            "event_id": "evt_rev_thermal_comm2",
            "passage_end": 106,
            "passage_start": 62,
            "relation": "direct",
            "relevant_passage": "I benchmarked deadband tuning in simulation.",
            "source_group": "thread:acme-eng/thermal-control-system#12",
            "source_link": "https://github.com/acme-eng/thermal-control-system/issues/12#issuecomment-102",
            "source_type": "pr_review_comment",
            "title": "Sarah on Issue #12: Benchmark results against deadband tuning",
            "url_format_ok": true
          }
        ],
        "discussion_events": [],
        "evidence_assessment": {
          "label": "weak"
        },
        "evidence_events": [
          {
            "artifacts_touched": [
              "src/thermal/control.py"
            ],
            "author": "marcus_vance",
            "body": "We could tighten the deadband on the simple threshold on-off controller to +/- 1.5C. That requires zero external math libraries.",
            "event_id": "evt_rev_thermal_comm1",
            "parent_event_ids": [
              "evt_issue_thermal_12"
            ],
            "raw_metadata": {},
            "repo": "acme-eng/thermal-control-system",
            "repo_full_name": "acme-eng/thermal-control-system",
            "source_id": "c101",
            "source_type": "pr_review_comment",
            "source_url": "https://github.com/acme-eng/thermal-control-system/issues/12#issuecomment-101",
            "title": "Marcus on Issue #12: Proposed deadband tuning",
            "ts": "2026-01-11T11:20:00Z"
          },
          {
            "artifacts_touched": [
              "src/thermal/control.py"
            ],
            "author": "sarah_chen",
            "body": "I benchmarked deadband tuning in simulation. It increased latency by 17% and still caused a 6.2C overshoot on rapid thermal transient. We must reject on-off hysteresis and move to continuous PID control.",
            "event_id": "evt_rev_thermal_comm2",
            "parent_event_ids": [
              "evt_issue_thermal_12"
            ],
            "raw_metadata": {},
            "repo": "acme-eng/thermal-control-system",
            "repo_full_name": "acme-eng/thermal-control-system",
            "source_id": "c102",
            "source_type": "pr_review_comment",
            "source_url": "https://github.com/acme-eng/thermal-control-system/issues/12#issuecomment-102",
            "title": "Sarah on Issue #12: Benchmark results against deadband tuning",
            "ts": "2026-01-12T14:45:00Z"
          }
        ],
        "indirect_support": [],
        "lifecycle_state": "rejected",
        "missing_corroboration": [
          "no independent corroborating source recorded (single source group)"
        ],
        "needs_review": true,
        "state_history": [
          {
            "changed_at": "2026-01-12T15:00:00Z",
            "changed_by": "sarah_chen",
            "decision_id": "dec_thermal_deadband_rejected",
            "from_state": null,
            "history_id": "hist_init_dec_thermal_deadband_rejected_1792750872454028600_a15b1d",
            "notes": "Initial state: rejected. Reason: Tested in simulation following Issue #12; deadband was insufficient to prevent emergency chamber thermal trip.",
            "reconstructed": 0,
            "repo_full_name": "acme-eng/thermal-control-system",
            "state": "rejected"
          }
        ]
      },
      "status": "success"
    },
    "dec_thermal_pid_01": {
      "data": {
        "conflicting_evidence": [],
        "decision": {
          "alternatives_considered": [],
          "alternatives_json": "[]",
          "confidence": 0.8,
          "decision_id": "dec_thermal_pid_01",
          "evidence_assessment": "insufficient",
          "freshness": "fresh",
          "made_at": "2026-01-15T16:00:00Z",
          "made_by": "sarah_chen",
          "rationale": "Governing architectural baseline decision",
          "repo": "acme-eng/thermal-control-system",
          "repo_full_name": "acme-eng/thermal-control-system",
          "review_status": "pending_review",
          "state": "accepted",
          "superseded_by_decision_id": null,
          "supersedes_decision_id": null,
          "title": "Architectural Decision dec_thermal_pid_01"
        },
        "direct_support": [],
        "discussion_events": [],
        "evidence_assessment": {
          "label": "insufficient"
        },
        "evidence_events": [
          {
            "artifacts_touched": [
              "src/thermal/control.py"
            ],
            "author": "sarah_chen",
            "body": "I benchmarked deadband tuning in simulation. It increased latency by 17% and still caused a 6.2C overshoot on rapid thermal transient. We must reject on-off hysteresis and move to continuous PID control.",
            "event_id": "evt_rev_thermal_comm2",
            "parent_event_ids": [
              "evt_issue_thermal_12"
            ],
            "raw_metadata": {},
            "repo": "acme-eng/thermal-control-system",
            "repo_full_name": "acme-eng/thermal-control-system",
            "source_id": "c102",
            "source_type": "pr_review_comment",
            "source_url": "https://github.com/acme-eng/thermal-control-system/issues/12#issuecomment-102",
            "title": "Sarah on Issue #12: Benchmark results against deadband tuning",
            "ts": "2026-01-12T14:45:00Z"
          }
        ],
        "indirect_support": [
          {
            "author": "sarah_chen",
            "date": "2026-01-12T14:45:00Z",
            "event_id": "evt_rev_thermal_comm2",
            "passage_end": null,
            "passage_start": null,
            "relation": "indirect",
            "relevant_passage": null,
            "source_group": "thread:acme-eng/thermal-control-system#12",
            "source_link": "https://github.com/acme-eng/thermal-control-system/issues/12#issuecomment-102",
            "source_type": "pr_review_comment",
            "title": "Sarah on Issue #12: Benchmark results against deadband tuning",
            "url_format_ok": true
          }
        ],
        "lifecycle_state": "accepted",
        "missing_corroboration": [
          "no independent corroborating source recorded (single source group)",
          "no direct passage evidence supporting claims (indirect only)",
          "no outcome/test evidence linked"
        ],
        "needs_review": true,
        "state_history": [
          {
            "changed_at": "2026-01-15T16:00:00Z",
            "changed_by": "sarah_chen",
            "decision_id": "dec_thermal_pid_01",
            "from_state": null,
            "history_id": "hist_init_dec_thermal_pid_01_1792750873097853300_cad87c",
            "notes": "Initial state: accepted. Reason: Governing architectural baseline decision",
            "reconstructed": 0,
            "repo_full_name": "acme-eng/thermal-control-system",
            "state": "accepted"
          }
        ]
      },
      "status": "success"
    },
    "dec_thermal_pid_accepted": {
      "data": {
        "conflicting_evidence": [
          {
            "event_id": "evt_adr_thermal_0004",
            "passage_text": "Deadband tuning was tested and rejected because it increased control latency by 17% and failed transient tests.",
            "relation": "contradicting",
            "source_group": "doc:acme-eng/thermal-control-system:docs/adr/0004-pid-thermal-regulation.md",
            "type": "contradicting_passage"
          }
        ],
        "decision": {
          "alternatives_considered": [
            {
              "description": "On-off hysteresis deadband controller",
              "evidence_event_ids": [
                "evt_rev_thermal_comm2"
              ],
              "rejection_reason": "Caused 17% latency increase and 6.2C overshoot in thermal transient tests"
            }
          ],
          "alternatives_json": "[{\"description\": \"On-off hysteresis deadband controller\", \"rejection_reason\": \"Caused 17% latency increase and 6.2C overshoot in thermal transient tests\", \"evidence_event_ids\": [\"evt_rev_thermal_comm2\"]}]",
          "confidence": 0.98,
          "decision_id": "dec_thermal_pid_accepted",
          "evidence_assessment": "insufficient",
          "freshness": "fresh",
          "made_at": "2026-01-15T16:00:00Z",
          "made_by": "sarah_chen",
          "rationale": "ADR 0004: Continuous PID loop with anti-windup clamping guarantees stability within +/- 0.4C of setpoint under heavy duty cycle.",
          "repo": "acme-eng/thermal-control-system",
          "repo_full_name": "acme-eng/thermal-control-system",
          "review_status": "auto_confirmed",
          "state": "accepted",
          "superseded_by_decision_id": null,
          "supersedes_decision_id": null,
          "title": "Adopt Discrete PID Controller for Chamber Temperature Regulation"
        },
        "direct_support": [
          {
            "author": "sarah_chen",
            "date": "2026-01-18T10:00:00Z",
            "event_id": "evt_git_thermal_a1b2c3d4",
            "passage_end": 135,
            "passage_start": 79,
            "relation": "direct",
            "relevant_passage": "Replaces on-off controller with discrete PID controller.",
            "source_group": "commit:a1b2c3d4e5f67890",
            "source_link": "https://github.com/acme-eng/thermal-control-system/commit/a1b2c3d4e5f67890",
            "source_type": "git_commit",
            "title": "feat(thermal): implement discrete PID controller with anti-windup (Closes #12)",
            "url_format_ok": true
          },
          {
            "author": "sarah_chen",
            "date": "2026-01-15T16:00:00Z",
            "event_id": "evt_adr_thermal_0004",
            "passage_end": 540,
            "passage_start": 525,
            "relation": "direct",
            "relevant_passage": "4C of setpoint.",
            "source_group": "doc:acme-eng/thermal-control-system:docs/adr/0004-pid-thermal-regulation.md",
            "source_link": "https://github.com/acme-eng/thermal-control-system/blob/main/docs/adr/0004-pid-thermal-regulation.md",
            "source_type": "adr",
            "title": "ADR 0004: Adopt Discrete PID Algorithm for Thermal Regulation",
            "url_format_ok": true
          },
          {
            "author": "sarah_chen",
            "date": "2026-01-18T10:00:00Z",
            "event_id": "evt_git_thermal_a1b2c3d4",
            "passage_end": 156,
            "passage_start": 136,
            "relation": "direct",
            "relevant_passage": "Implements ADR 0004.",
            "source_group": "commit:a1b2c3d4e5f67890",
            "source_link": "https://github.com/acme-eng/thermal-control-system/commit/a1b2c3d4e5f67890",
            "source_type": "git_commit",
            "title": "feat(thermal): implement discrete PID controller with anti-windup (Closes #12)",
            "url_format_ok": true
          }
        ],
        "discussion_events": [],
        "evidence_assessment": {
          "label": "contradicted"
        },
        "evidence_events": [
          {
            "artifacts_touched": [
              "src/thermal/control.py",
              "docs/adr/0004-pid-thermal-regulation.md"
            ],
            "author": "sarah_chen",
            "body": "Status: accepted\n\nContext:\nPrevious bang-bang / on-off controller caused severe thermal oscillations and triggered chamber shutdown (Issue #12). Deadband tuning was tested and rejected because it increased control latency by 17% and failed transient tests.\n\nDecision:\nImplement discrete PID control with anti-windup clamping in regulate_temperature(). Use scipy interpolation for telemetry curve smoothing.\n\nConsequences:\n- Smooth thermal trajectory within +/- 0.4C of setpoint.\n- Added dependency on scipy.\n- Slightly higher CPU compute per control cycle.",
            "event_id": "evt_adr_thermal_0004",
            "parent_event_ids": [],
            "raw_metadata": {
              "parsed_adr": {
                "consequences": "Maintains temperature within +/- 0.4C setpoint with anti-windup.",
                "context": "Previous bang-bang / on-off controller caused severe thermal oscillations. Deadband tuning increased latency by 17%.",
                "decision": "Implement discrete PID control with anti-windup clamping in regulate_temperature().",
                "status": "accepted",
                "title": "Adopt Discrete PID Algorithm for Thermal Regulation"
              }
            },
            "repo": "acme-eng/thermal-control-system",
            "repo_full_name": "acme-eng/thermal-control-system",
            "source_id": "docs/adr/0004-pid-thermal-regulation.md",
            "source_type": "adr",
            "source_url": "https://github.com/acme-eng/thermal-control-system/blob/main/docs/adr/0004-pid-thermal-regulation.md",
            "title": "ADR 0004: Adopt Discrete PID Algorithm for Thermal Regulation",
            "ts": "2026-01-15T16:00:00Z"
          },
          {
            "artifacts_touched": [
              "src/thermal/control.py",
              "requirements.txt"
            ],
            "author": "sarah_chen",
            "body": "Replaces on-off controller with discrete PID controller. Implements ADR 0004. Closes #12.",
            "event_id": "evt_git_thermal_a1b2c3d4",
            "parent_event_ids": [
              "evt_issue_thermal_12"
            ],
            "raw_metadata": {
              "diff_summary": "@@ -14,6 +14,24 @@ def regulate_temperature(current_temp, target_temp):\n- if current_temp > target_temp: fan_on()\n+ error = target_temp - current_temp\n+ p_term = Kp * error\n+ i_term = Ki * (integral + error * dt)\n+ output = clamp(p_term + i_term + d_term, 0.0, 100.0)"
            },
            "repo": "acme-eng/thermal-control-system",
            "repo_full_name": "acme-eng/thermal-control-system",
            "source_id": "a1b2c3d4e5f67890",
            "source_type": "git_commit",
            "source_url": "https://github.com/acme-eng/thermal-control-system/commit/a1b2c3d4e5f67890",
            "title": "feat(thermal): implement discrete PID controller with anti-windup (Closes #12)",
            "ts": "2026-01-18T10:00:00Z"
          }
        ],
        "indirect_support": [],
        "lifecycle_state": "accepted",
        "missing_corroboration": [],
        "needs_review": true,
        "state_history": [
          {
            "changed_at": "2026-01-15T16:00:00Z",
            "changed_by": "sarah_chen",
            "decision_id": "dec_thermal_pid_accepted",
            "from_state": null,
            "history_id": "hist_init_dec_thermal_pid_accepted_1792750872538100900_e9e923",
            "notes": "Initial state: accepted. Reason: ADR 0004: Continuous PID loop with anti-windup clamping guarantees stability within +/- 0.4C of setpoint under heavy duty cycle.",
            "reconstructed": 0,
            "repo_full_name": "acme-eng/thermal-control-system",
            "state": "accepted"
          }
        ]
      },
      "status": "success"
    }
  },
  "explains": {
    "deps::redis": {
      "data": {
        "artifact": "deps::redis",
        "chain": [
          {
            "conflicting_evidence": [
              {
                "event_id": "evt_rev_cache_c201",
                "passage_text": "Priya review on PR #38: In-memory cache cannot scale across replicas",
                "relation": "contradicting",
                "source_group": "thread:acme-eng/distributed-cache-service#38",
                "type": "contradicting_passage"
              },
              {
                "decision_id": "dec_cache_local_lru_proposed",
                "made_at": "2026-02-03T14:30:00Z",
                "state": "superseded",
                "title": "Retain In-Memory LRU Cache with Process Memory Cap",
                "type": "related_decision_on_entity"
              }
            ],
            "decision": {
              "decision_id": "dec_cache_redis_accepted",
              "made_at": "2026-02-06T15:00:00Z",
              "made_by": "priya_patel",
              "rationale": "ADR 0009: Decommission local in-memory dict and migrate to Redis cluster to prevent container OOMs and maintain cache consistency across autoscaled pods.",
              "repo": "acme-eng/distributed-cache-service",
              "title": "Migrate from In-Memory LRU to Distributed Redis Cluster"
            },
            "decision_id": "dec_cache_redis_accepted",
            "direct_support": [
              {
                "author": "priya_patel",
                "date": "2026-02-06T15:00:00Z",
                "event_id": "evt_adr_cache_0009",
                "passage_end": 282,
                "passage_start": 169,
                "relation": "direct",
                "relevant_passage": "PR #38 attempted local memory capping but was rejected because container autoscaling requires shared cache state.",
                "source_group": "doc:acme-eng/distributed-cache-service:docs/adr/0009-redis-cluster-cache.md",
                "source_link": "https://github.com/acme-eng/distributed-cache-service/blob/main/docs/adr/0009-redis-cluster-cache.md",
                "source_type": "adr",
                "title": "ADR 0009: Migrate to Redis Cluster for Distributed Caching",
                "url_format_ok": true
              },
              {
                "author": "priya_patel",
                "date": "2026-02-06T15:00:00Z",
                "event_id": "evt_adr_cache_0009",
                "passage_end": 58,
                "passage_start": 0,
                "relation": "direct",
                "relevant_passage": "ADR 0009: Migrate to Redis Cluster for Distributed Caching",
                "source_group": "doc:acme-eng/distributed-cache-service:docs/adr/0009-redis-cluster-cache.md",
                "source_link": "https://github.com/acme-eng/distributed-cache-service/blob/main/docs/adr/0009-redis-cluster-cache.md",
                "source_type": "adr",
                "title": "ADR 0009: Migrate to Redis Cluster for Distributed Caching",
                "url_format_ok": true
              },
              {
                "author": "priya_patel",
                "date": "2026-02-04T09:00:00Z",
                "event_id": "evt_rev_cache_c201",
                "passage_end": 220,
                "passage_start": 184,
                "relation": "direct",
                "relevant_passage": "We need a distributed Redis cluster.",
                "source_group": "thread:acme-eng/distributed-cache-service#38",
                "source_link": "https://github.com/acme-eng/distributed-cache-service/pull/38#discussion_r201",
                "source_type": "pr_review_comment",
                "title": "Priya review on PR #38: In-memory cache cannot scale across replicas",
                "url_format_ok": true
              }
            ],
            "evidence_assessment": {
              "label": "contradicted"
            },
            "indirect_support": [],
            "lifecycle_state": "accepted",
            "made_at": "2026-02-06T15:00:00Z",
            "made_by": "priya_patel",
            "missing_corroboration": [
              "no outcome/test evidence linked"
            ],
            "needs_review": true,
            "rationale": "ADR 0009: Decommission local in-memory dict and migrate to Redis cluster to prevent container OOMs and maintain cache consistency across autoscaled pods.",
            "state": "accepted",
            "step_number": 1,
            "summary": "[ACCEPTED] Migrate from In-Memory LRU to Distributed Redis Cluster (by priya_patel on 2026-02-06)",
            "title": "Migrate from In-Memory LRU to Distributed Redis Cluster"
          }
        ],
        "citations": [
          {
            "author": "priya_patel",
            "passage": "PR #38 attempted local memory capping but was rejected because container autoscaling requires shared cache state.",
            "relation": "direct",
            "source_id": "evt_adr_cache_0009",
            "source_type": "adr",
            "source_url": "https://github.com/acme-eng/distributed-cache-service/blob/main/docs/adr/0009-redis-cluster-cache.md",
            "timestamp": "2026-02-06T15:00:00Z",
            "title": "ADR 0009: Migrate to Redis Cluster for Distributed Caching"
          },
          {
            "author": "priya_patel",
            "passage": "ADR 0009: Migrate to Redis Cluster for Distributed Caching",
            "relation": "direct",
            "source_id": "evt_adr_cache_0009",
            "source_type": "adr",
            "source_url": "https://github.com/acme-eng/distributed-cache-service/blob/main/docs/adr/0009-redis-cluster-cache.md",
            "timestamp": "2026-02-06T15:00:00Z",
            "title": "ADR 0009: Migrate to Redis Cluster for Distributed Caching"
          },
          {
            "author": "priya_patel",
            "passage": "We need a distributed Redis cluster.",
            "relation": "direct",
            "source_id": "evt_rev_cache_c201",
            "source_type": "pr_review_comment",
            "source_url": "https://github.com/acme-eng/distributed-cache-service/pull/38#discussion_r201",
            "timestamp": "2026-02-04T09:00:00Z",
            "title": "Priya review on PR #38: In-memory cache cannot scale across replicas"
          }
        ],
        "claim_support_rate": 0.0,
        "conflicting_evidence": [
          {
            "event_id": "evt_rev_cache_c201",
            "passage_text": "Priya review on PR #38: In-memory cache cannot scale across replicas",
            "relation": "contradicting",
            "source_group": "thread:acme-eng/distributed-cache-service#38",
            "type": "contradicting_passage"
          },
          {
            "decision_id": "dec_cache_local_lru_proposed",
            "made_at": "2026-02-03T14:30:00Z",
            "state": "superseded",
            "title": "Retain In-Memory LRU Cache with Process Memory Cap",
            "type": "related_decision_on_entity"
          }
        ],
        "current_decision": "Migrate from In-Memory LRU to Distributed Redis Cluster",
        "current_state": "accepted",
        "decision": {
          "decision_id": "dec_cache_redis_accepted",
          "made_at": "2026-02-06T15:00:00Z",
          "made_by": "priya_patel",
          "rationale": "ADR 0009: Decommission local in-memory dict and migrate to Redis cluster to prevent container OOMs and maintain cache consistency across autoscaled pods.",
          "repo": "acme-eng/distributed-cache-service",
          "title": "Migrate from In-Memory LRU to Distributed Redis Cluster"
        },
        "direct_support": [
          {
            "author": "priya_patel",
            "date": "2026-02-06T15:00:00Z",
            "event_id": "evt_adr_cache_0009",
            "passage_end": 282,
            "passage_start": 169,
            "relation": "direct",
            "relevant_passage": "PR #38 attempted local memory capping but was rejected because container autoscaling requires shared cache state.",
            "source_group": "doc:acme-eng/distributed-cache-service:docs/adr/0009-redis-cluster-cache.md",
            "source_link": "https://github.com/acme-eng/distributed-cache-service/blob/main/docs/adr/0009-redis-cluster-cache.md",
            "source_type": "adr",
            "title": "ADR 0009: Migrate to Redis Cluster for Distributed Caching",
            "url_format_ok": true
          },
          {
            "author": "priya_patel",
            "date": "2026-02-06T15:00:00Z",
            "event_id": "evt_adr_cache_0009",
            "passage_end": 58,
            "passage_start": 0,
            "relation": "direct",
            "relevant_passage": "ADR 0009: Migrate to Redis Cluster for Distributed Caching",
            "source_group": "doc:acme-eng/distributed-cache-service:docs/adr/0009-redis-cluster-cache.md",
            "source_link": "https://github.com/acme-eng/distributed-cache-service/blob/main/docs/adr/0009-redis-cluster-cache.md",
            "source_type": "adr",
            "title": "ADR 0009: Migrate to Redis Cluster for Distributed Caching",
            "url_format_ok": true
          },
          {
            "author": "priya_patel",
            "date": "2026-02-04T09:00:00Z",
            "event_id": "evt_rev_cache_c201",
            "passage_end": 220,
            "passage_start": 184,
            "relation": "direct",
            "relevant_passage": "We need a distributed Redis cluster.",
            "source_group": "thread:acme-eng/distributed-cache-service#38",
            "source_link": "https://github.com/acme-eng/distributed-cache-service/pull/38#discussion_r201",
            "source_type": "pr_review_comment",
            "title": "Priya review on PR #38: In-memory cache cannot scale across replicas",
            "url_format_ok": true
          }
        ],
        "evidence_assessment": {
          "label": "contradicted"
        },
        "explanation": "Artifact 'deps::redis' is governed primarily by accepted decision 'Migrate from In-Memory LRU to Distributed Redis Cluster', established by priya_patel on 2026-02-06.\n\nKey Rationale: ADR 0009: Decommission local in-memory dict and migrate to Redis cluster to prevent container OOMs and maintain cache consistency across autoscaled pods.\n\n",
        "indirect_support": [],
        "lifecycle_state": "accepted",
        "missing_corroboration": [
          "no outcome/test evidence linked"
        ],
        "needs_review": true,
        "statements": [
          {
            "event_id": "evt_adr_cache_0009",
            "flagged_unsupported": true,
            "overlap_ratio": 0.27,
            "passage": "PR #38 attempted local memory capping but was rejected because container autoscaling requires shared cache state.",
            "source_link": "https://github.com/acme-eng/distributed-cache-service/blob/main/docs/adr/0009-redis-cluster-cache.md",
            "supported": false,
            "text": "Artifact 'deps::redis' is governed primarily by accepted decision 'Migrate from In-Memory LRU to Distributed Redis Cluster', established by priya_patel on 2026-02-06."
          },
          {
            "event_id": "evt_adr_cache_0009",
            "flagged_unsupported": true,
            "overlap_ratio": 0.39,
            "passage": "PR #38 attempted local memory capping but was rejected because container autoscaling requires shared cache state.",
            "source_link": "https://github.com/acme-eng/distributed-cache-service/blob/main/docs/adr/0009-redis-cluster-cache.md",
            "supported": false,
            "text": "Key Rationale: ADR 0009: Decommission local in-memory dict and migrate to Redis cluster to prevent container OOMs and maintain cache consistency across autoscaled pods."
          }
        ],
        "status": "grounded",
        "unsupported_sentences": [
          "Artifact 'deps::redis' is governed primarily by accepted decision 'Migrate from In-Memory LRU to Distributed Redis Cluster', established by priya_patel on 2026-02-06.",
          "Key Rationale: ADR 0009: Decommission local in-memory dict and migrate to Redis cluster to prevent container OOMs and maintain cache consistency across autoscaled pods."
        ]
      },
      "status": "success"
    },
    "deps::scipy": {
      "data": {
        "artifact": "deps::scipy",
        "chain": [
          {
            "conflicting_evidence": [
              {
                "event_id": "evt_adr_thermal_0004",
                "passage_text": "Deadband tuning was tested and rejected because it increased control latency by 17% and failed transient tests.",
                "relation": "contradicting",
                "source_group": "doc:acme-eng/thermal-control-system:docs/adr/0004-pid-thermal-regulation.md",
                "type": "contradicting_passage"
              }
            ],
            "decision": {
              "decision_id": "dec_thermal_pid_accepted",
              "made_at": "2026-01-15T16:00:00Z",
              "made_by": "sarah_chen",
              "rationale": "ADR 0004: Continuous PID loop with anti-windup clamping guarantees stability within +/- 0.4C of setpoint under heavy duty cycle.",
              "repo": "acme-eng/thermal-control-system",
              "title": "Adopt Discrete PID Controller for Chamber Temperature Regulation"
            },
            "decision_id": "dec_thermal_pid_accepted",
            "direct_support": [
              {
                "author": "sarah_chen",
                "date": "2026-01-18T10:00:00Z",
                "event_id": "evt_git_thermal_a1b2c3d4",
                "passage_end": 135,
                "passage_start": 79,
                "relation": "direct",
                "relevant_passage": "Replaces on-off controller with discrete PID controller.",
                "source_group": "commit:a1b2c3d4e5f67890",
                "source_link": "https://github.com/acme-eng/thermal-control-system/commit/a1b2c3d4e5f67890",
                "source_type": "git_commit",
                "title": "feat(thermal): implement discrete PID controller with anti-windup (Closes #12)",
                "url_format_ok": true
              },
              {
                "author": "sarah_chen",
                "date": "2026-01-15T16:00:00Z",
                "event_id": "evt_adr_thermal_0004",
                "passage_end": 540,
                "passage_start": 525,
                "relation": "direct",
                "relevant_passage": "4C of setpoint.",
                "source_group": "doc:acme-eng/thermal-control-system:docs/adr/0004-pid-thermal-regulation.md",
                "source_link": "https://github.com/acme-eng/thermal-control-system/blob/main/docs/adr/0004-pid-thermal-regulation.md",
                "source_type": "adr",
                "title": "ADR 0004: Adopt Discrete PID Algorithm for Thermal Regulation",
                "url_format_ok": true
              },
              {
                "author": "sarah_chen",
                "date": "2026-01-18T10:00:00Z",
                "event_id": "evt_git_thermal_a1b2c3d4",
                "passage_end": 156,
                "passage_start": 136,
                "relation": "direct",
                "relevant_passage": "Implements ADR 0004.",
                "source_group": "commit:a1b2c3d4e5f67890",
                "source_link": "https://github.com/acme-eng/thermal-control-system/commit/a1b2c3d4e5f67890",
                "source_type": "git_commit",
                "title": "feat(thermal): implement discrete PID controller with anti-windup (Closes #12)",
                "url_format_ok": true
              }
            ],
            "evidence_assessment": {
              "label": "contradicted"
            },
            "indirect_support": [],
            "lifecycle_state": "accepted",
            "made_at": "2026-01-15T16:00:00Z",
            "made_by": "sarah_chen",
            "missing_corroboration": [],
            "needs_review": true,
            "rationale": "ADR 0004: Continuous PID loop with anti-windup clamping guarantees stability within +/- 0.4C of setpoint under heavy duty cycle.",
            "state": "accepted",
            "step_number": 1,
            "summary": "[ACCEPTED] Adopt Discrete PID Controller for Chamber Temperature Regulation (by sarah_chen on 2026-01-15)",
            "title": "Adopt Discrete PID Controller for Chamber Temperature Regulation"
          }
        ],
        "citations": [
          {
            "author": "sarah_chen",
            "passage": "Replaces on-off controller with discrete PID controller.",
            "relation": "direct",
            "source_id": "evt_git_thermal_a1b2c3d4",
            "source_type": "git_commit",
            "source_url": "https://github.com/acme-eng/thermal-control-system/commit/a1b2c3d4e5f67890",
            "timestamp": "2026-01-18T10:00:00Z",
            "title": "feat(thermal): implement discrete PID controller with anti-windup (Closes #12)"
          },
          {
            "author": "sarah_chen",
            "passage": "4C of setpoint.",
            "relation": "direct",
            "source_id": "evt_adr_thermal_0004",
            "source_type": "adr",
            "source_url": "https://github.com/acme-eng/thermal-control-system/blob/main/docs/adr/0004-pid-thermal-regulation.md",
            "timestamp": "2026-01-15T16:00:00Z",
            "title": "ADR 0004: Adopt Discrete PID Algorithm for Thermal Regulation"
          },
          {
            "author": "sarah_chen",
            "passage": "Implements ADR 0004.",
            "relation": "direct",
            "source_id": "evt_git_thermal_a1b2c3d4",
            "source_type": "git_commit",
            "source_url": "https://github.com/acme-eng/thermal-control-system/commit/a1b2c3d4e5f67890",
            "timestamp": "2026-01-18T10:00:00Z",
            "title": "feat(thermal): implement discrete PID controller with anti-windup (Closes #12)"
          }
        ],
        "claim_support_rate": 0.0,
        "conflicting_evidence": [
          {
            "event_id": "evt_adr_thermal_0004",
            "passage_text": "Deadband tuning was tested and rejected because it increased control latency by 17% and failed transient tests.",
            "relation": "contradicting",
            "source_group": "doc:acme-eng/thermal-control-system:docs/adr/0004-pid-thermal-regulation.md",
            "type": "contradicting_passage"
          }
        ],
        "current_decision": "Adopt Discrete PID Controller for Chamber Temperature Regulation",
        "current_state": "accepted",
        "decision": {
          "decision_id": "dec_thermal_pid_accepted",
          "made_at": "2026-01-15T16:00:00Z",
          "made_by": "sarah_chen",
          "rationale": "ADR 0004: Continuous PID loop with anti-windup clamping guarantees stability within +/- 0.4C of setpoint under heavy duty cycle.",
          "repo": "acme-eng/thermal-control-system",
          "title": "Adopt Discrete PID Controller for Chamber Temperature Regulation"
        },
        "direct_support": [
          {
            "author": "sarah_chen",
            "date": "2026-01-18T10:00:00Z",
            "event_id": "evt_git_thermal_a1b2c3d4",
            "passage_end": 135,
            "passage_start": 79,
            "relation": "direct",
            "relevant_passage": "Replaces on-off controller with discrete PID controller.",
            "source_group": "commit:a1b2c3d4e5f67890",
            "source_link": "https://github.com/acme-eng/thermal-control-system/commit/a1b2c3d4e5f67890",
            "source_type": "git_commit",
            "title": "feat(thermal): implement discrete PID controller with anti-windup (Closes #12)",
            "url_format_ok": true
          },
          {
            "author": "sarah_chen",
            "date": "2026-01-15T16:00:00Z",
            "event_id": "evt_adr_thermal_0004",
            "passage_end": 540,
            "passage_start": 525,
            "relation": "direct",
            "relevant_passage": "4C of setpoint.",
            "source_group": "doc:acme-eng/thermal-control-system:docs/adr/0004-pid-thermal-regulation.md",
            "source_link": "https://github.com/acme-eng/thermal-control-system/blob/main/docs/adr/0004-pid-thermal-regulation.md",
            "source_type": "adr",
            "title": "ADR 0004: Adopt Discrete PID Algorithm for Thermal Regulation",
            "url_format_ok": true
          },
          {
            "author": "sarah_chen",
            "date": "2026-01-18T10:00:00Z",
            "event_id": "evt_git_thermal_a1b2c3d4",
            "passage_end": 156,
            "passage_start": 136,
            "relation": "direct",
            "relevant_passage": "Implements ADR 0004.",
            "source_group": "commit:a1b2c3d4e5f67890",
            "source_link": "https://github.com/acme-eng/thermal-control-system/commit/a1b2c3d4e5f67890",
            "source_type": "git_commit",
            "title": "feat(thermal): implement discrete PID controller with anti-windup (Closes #12)",
            "url_format_ok": true
          }
        ],
        "evidence_assessment": {
          "label": "contradicted"
        },
        "explanation": "Artifact 'deps::scipy' is governed primarily by accepted decision 'Adopt Discrete PID Controller for Chamber Temperature Regulation', established by sarah_chen on 2026-01-15.\n\nKey Rationale: ADR 0004: Continuous PID loop with anti-windup clamping guarantees stability within +/- 0.4C of setpoint under heavy duty cycle.\n\n",
        "indirect_support": [],
        "lifecycle_state": "accepted",
        "missing_corroboration": [],
        "needs_review": true,
        "statements": [
          {
            "event_id": "evt_adr_thermal_0004",
            "flagged_unsupported": true,
            "overlap_ratio": 0.19,
            "passage": "4C of setpoint.",
            "source_link": "https://github.com/acme-eng/thermal-control-system/blob/main/docs/adr/0004-pid-thermal-regulation.md",
            "supported": false,
            "text": "Artifact 'deps::scipy' is governed primarily by accepted decision 'Adopt Discrete PID Controller for Chamber Temperature Regulation', established by sarah_chen on 2026-01-15."
          },
          {
            "event_id": "evt_adr_thermal_0004",
            "flagged_unsupported": true,
            "overlap_ratio": 0.15,
            "passage": "4C of setpoint.",
            "source_link": "https://github.com/acme-eng/thermal-control-system/blob/main/docs/adr/0004-pid-thermal-regulation.md",
            "supported": false,
            "text": "Key Rationale: ADR 0004: Continuous PID loop with anti-windup clamping guarantees stability within +/- 0.4C of setpoint under heavy duty cycle."
          }
        ],
        "status": "grounded",
        "unsupported_sentences": [
          "Artifact 'deps::scipy' is governed primarily by accepted decision 'Adopt Discrete PID Controller for Chamber Temperature Regulation', established by sarah_chen on 2026-01-15.",
          "Key Rationale: ADR 0004: Continuous PID loop with anti-windup clamping guarantees stability within +/- 0.4C of setpoint under heavy duty cycle."
        ]
      },
      "status": "success"
    },
    "docs/adr/0004-pid-thermal-regulation.md": {
      "data": {
        "artifact": "docs/adr/0004-pid-thermal-regulation.md",
        "chain": [],
        "citations": [],
        "claim_support_rate": 0.0,
        "explanation": "No recorded architectural decisions found for artifact 'docs/adr/0004-pid-thermal-regulation.md' in project history.",
        "statements": [],
        "status": "not_found",
        "unsupported_sentences": []
      },
      "status": "success"
    },
    "src/cache/store.py": {
      "data": {
        "artifact": "src/cache/store.py",
        "chain": [
          {
            "conflicting_evidence": [
              {
                "decision_id": "dec_cache_redis_accepted",
                "made_at": "2026-02-06T15:00:00Z",
                "state": "accepted",
                "title": "Migrate from In-Memory LRU to Distributed Redis Cluster",
                "type": "related_decision_on_entity"
              }
            ],
            "decision": {
              "decision_id": "dec_cache_local_lru_proposed",
              "made_at": "2026-02-03T14:30:00Z",
              "made_by": "marcus_vance",
              "rationale": "Keep cache strictly inside Python heap to guarantee sub-millisecond access and avoid external Redis infra.",
              "repo": "acme-eng/distributed-cache-service",
              "title": "Retain In-Memory LRU Cache with Process Memory Cap"
            },
            "decision_id": "dec_cache_local_lru_proposed",
            "direct_support": [
              {
                "author": "marcus_vance",
                "date": "2026-02-03T14:30:00Z",
                "event_id": "evt_pr_cache_38",
                "passage_end": 203,
                "passage_start": 155,
                "relation": "direct",
                "relevant_passage": "Keeps caching local with sub-millisecond access.",
                "source_group": "thread:acme-eng/distributed-cache-service#38",
                "source_link": "https://github.com/acme-eng/distributed-cache-service/pull/38",
                "source_type": "github_pr",
                "title": "PR #38: Add soft memory cap to in-memory LRU cache (Closes #34)",
                "url_format_ok": true
              }
            ],
            "evidence_assessment": {
              "label": "weak"
            },
            "indirect_support": [
              {
                "author": "marcus_vance",
                "date": "2026-02-03T14:30:00Z",
                "event_id": "evt_pr_cache_38",
                "passage_end": null,
                "passage_start": null,
                "relation": "indirect",
                "relevant_passage": null,
                "source_group": "thread:acme-eng/distributed-cache-service#38",
                "source_link": "https://github.com/acme-eng/distributed-cache-service/pull/38",
                "source_type": "github_pr",
                "title": "PR #38: Add soft memory cap to in-memory LRU cache (Closes #34)",
                "url_format_ok": true
              }
            ],
            "lifecycle_state": "superseded",
            "made_at": "2026-02-03T14:30:00Z",
            "made_by": "marcus_vance",
            "missing_corroboration": [
              "no independent corroborating source recorded (single source group)",
              "no outcome/test evidence linked"
            ],
            "needs_review": true,
            "rationale": "Keep cache strictly inside Python heap to guarantee sub-millisecond access and avoid external Redis infra.",
            "state": "superseded",
            "step_number": 1,
            "summary": "[SUPERSEDED] Retain In-Memory LRU Cache with Process Memory Cap (by marcus_vance on 2026-02-03)",
            "title": "Retain In-Memory LRU Cache with Process Memory Cap"
          },
          {
            "conflicting_evidence": [
              {
                "event_id": "evt_rev_cache_c201",
                "passage_text": "Priya review on PR #38: In-memory cache cannot scale across replicas",
                "relation": "contradicting",
                "source_group": "thread:acme-eng/distributed-cache-service#38",
                "type": "contradicting_passage"
              },
              {
                "decision_id": "dec_cache_local_lru_proposed",
                "made_at": "2026-02-03T14:30:00Z",
                "state": "superseded",
                "title": "Retain In-Memory LRU Cache with Process Memory Cap",
                "type": "related_decision_on_entity"
              }
            ],
            "decision": {
              "decision_id": "dec_cache_redis_accepted",
              "made_at": "2026-02-06T15:00:00Z",
              "made_by": "priya_patel",
              "rationale": "ADR 0009: Decommission local in-memory dict and migrate to Redis cluster to prevent container OOMs and maintain cache consistency across autoscaled pods.",
              "repo": "acme-eng/distributed-cache-service",
              "title": "Migrate from In-Memory LRU to Distributed Redis Cluster"
            },
            "decision_id": "dec_cache_redis_accepted",
            "direct_support": [
              {
                "author": "priya_patel",
                "date": "2026-02-06T15:00:00Z",
                "event_id": "evt_adr_cache_0009",
                "passage_end": 282,
                "passage_start": 169,
                "relation": "direct",
                "relevant_passage": "PR #38 attempted local memory capping but was rejected because container autoscaling requires shared cache state.",
                "source_group": "doc:acme-eng/distributed-cache-service:docs/adr/0009-redis-cluster-cache.md",
                "source_link": "https://github.com/acme-eng/distributed-cache-service/blob/main/docs/adr/0009-redis-cluster-cache.md",
                "source_type": "adr",
                "title": "ADR 0009: Migrate to Redis Cluster for Distributed Caching",
                "url_format_ok": true
              },
              {
                "author": "priya_patel",
                "date": "2026-02-06T15:00:00Z",
                "event_id": "evt_adr_cache_0009",
                "passage_end": 58,
                "passage_start": 0,
                "relation": "direct",
                "relevant_passage": "ADR 0009: Migrate to Redis Cluster for Distributed Caching",
                "source_group": "doc:acme-eng/distributed-cache-service:docs/adr/0009-redis-cluster-cache.md",
                "source_link": "https://github.com/acme-eng/distributed-cache-service/blob/main/docs/adr/0009-redis-cluster-cache.md",
                "source_type": "adr",
                "title": "ADR 0009: Migrate to Redis Cluster for Distributed Caching",
                "url_format_ok": true
              },
              {
                "author": "priya_patel",
                "date": "2026-02-04T09:00:00Z",
                "event_id": "evt_rev_cache_c201",
                "passage_end": 220,
                "passage_start": 184,
                "relation": "direct",
                "relevant_passage": "We need a distributed Redis cluster.",
                "source_group": "thread:acme-eng/distributed-cache-service#38",
                "source_link": "https://github.com/acme-eng/distributed-cache-service/pull/38#discussion_r201",
                "source_type": "pr_review_comment",
                "title": "Priya review on PR #38: In-memory cache cannot scale across replicas",
                "url_format_ok": true
              }
            ],
            "evidence_assessment": {
              "label": "contradicted"
            },
            "indirect_support": [],
            "lifecycle_state": "accepted",
            "made_at": "2026-02-06T15:00:00Z",
            "made_by": "priya_patel",
            "missing_corroboration": [
              "no outcome/test evidence linked"
            ],
            "needs_review": true,
            "rationale": "ADR 0009: Decommission local in-memory dict and migrate to Redis cluster to prevent container OOMs and maintain cache consistency across autoscaled pods.",
            "state": "accepted",
            "step_number": 2,
            "summary": "[ACCEPTED] Migrate from In-Memory LRU to Distributed Redis Cluster (by priya_patel on 2026-02-06)",
            "title": "Migrate from In-Memory LRU to Distributed Redis Cluster"
          }
        ],
        "citations": [
          {
            "author": "marcus_vance",
            "passage": "Keeps caching local with sub-millisecond access.",
            "relation": "direct",
            "source_id": "evt_pr_cache_38",
            "source_type": "github_pr",
            "source_url": "https://github.com/acme-eng/distributed-cache-service/pull/38",
            "timestamp": "2026-02-03T14:30:00Z",
            "title": "PR #38: Add soft memory cap to in-memory LRU cache (Closes #34)"
          },
          {
            "author": "priya_patel",
            "passage": "PR #38 attempted local memory capping but was rejected because container autoscaling requires shared cache state.",
            "relation": "direct",
            "source_id": "evt_adr_cache_0009",
            "source_type": "adr",
            "source_url": "https://github.com/acme-eng/distributed-cache-service/blob/main/docs/adr/0009-redis-cluster-cache.md",
            "timestamp": "2026-02-06T15:00:00Z",
            "title": "ADR 0009: Migrate to Redis Cluster for Distributed Caching"
          },
          {
            "author": "priya_patel",
            "passage": "ADR 0009: Migrate to Redis Cluster for Distributed Caching",
            "relation": "direct",
            "source_id": "evt_adr_cache_0009",
            "source_type": "adr",
            "source_url": "https://github.com/acme-eng/distributed-cache-service/blob/main/docs/adr/0009-redis-cluster-cache.md",
            "timestamp": "2026-02-06T15:00:00Z",
            "title": "ADR 0009: Migrate to Redis Cluster for Distributed Caching"
          },
          {
            "author": "priya_patel",
            "passage": "We need a distributed Redis cluster.",
            "relation": "direct",
            "source_id": "evt_rev_cache_c201",
            "source_type": "pr_review_comment",
            "source_url": "https://github.com/acme-eng/distributed-cache-service/pull/38#discussion_r201",
            "timestamp": "2026-02-04T09:00:00Z",
            "title": "Priya review on PR #38: In-memory cache cannot scale across replicas"
          }
        ],
        "claim_support_rate": 0.0,
        "conflicting_evidence": [
          {
            "event_id": "evt_rev_cache_c201",
            "passage_text": "Priya review on PR #38: In-memory cache cannot scale across replicas",
            "relation": "contradicting",
            "source_group": "thread:acme-eng/distributed-cache-service#38",
            "type": "contradicting_passage"
          },
          {
            "decision_id": "dec_cache_local_lru_proposed",
            "made_at": "2026-02-03T14:30:00Z",
            "state": "superseded",
            "title": "Retain In-Memory LRU Cache with Process Memory Cap",
            "type": "related_decision_on_entity"
          }
        ],
        "current_decision": "Migrate from In-Memory LRU to Distributed Redis Cluster",
        "current_state": "accepted",
        "decision": {
          "decision_id": "dec_cache_redis_accepted",
          "made_at": "2026-02-06T15:00:00Z",
          "made_by": "priya_patel",
          "rationale": "ADR 0009: Decommission local in-memory dict and migrate to Redis cluster to prevent container OOMs and maintain cache consistency across autoscaled pods.",
          "repo": "acme-eng/distributed-cache-service",
          "title": "Migrate from In-Memory LRU to Distributed Redis Cluster"
        },
        "direct_support": [
          {
            "author": "priya_patel",
            "date": "2026-02-06T15:00:00Z",
            "event_id": "evt_adr_cache_0009",
            "passage_end": 282,
            "passage_start": 169,
            "relation": "direct",
            "relevant_passage": "PR #38 attempted local memory capping but was rejected because container autoscaling requires shared cache state.",
            "source_group": "doc:acme-eng/distributed-cache-service:docs/adr/0009-redis-cluster-cache.md",
            "source_link": "https://github.com/acme-eng/distributed-cache-service/blob/main/docs/adr/0009-redis-cluster-cache.md",
            "source_type": "adr",
            "title": "ADR 0009: Migrate to Redis Cluster for Distributed Caching",
            "url_format_ok": true
          },
          {
            "author": "priya_patel",
            "date": "2026-02-06T15:00:00Z",
            "event_id": "evt_adr_cache_0009",
            "passage_end": 58,
            "passage_start": 0,
            "relation": "direct",
            "relevant_passage": "ADR 0009: Migrate to Redis Cluster for Distributed Caching",
            "source_group": "doc:acme-eng/distributed-cache-service:docs/adr/0009-redis-cluster-cache.md",
            "source_link": "https://github.com/acme-eng/distributed-cache-service/blob/main/docs/adr/0009-redis-cluster-cache.md",
            "source_type": "adr",
            "title": "ADR 0009: Migrate to Redis Cluster for Distributed Caching",
            "url_format_ok": true
          },
          {
            "author": "priya_patel",
            "date": "2026-02-04T09:00:00Z",
            "event_id": "evt_rev_cache_c201",
            "passage_end": 220,
            "passage_start": 184,
            "relation": "direct",
            "relevant_passage": "We need a distributed Redis cluster.",
            "source_group": "thread:acme-eng/distributed-cache-service#38",
            "source_link": "https://github.com/acme-eng/distributed-cache-service/pull/38#discussion_r201",
            "source_type": "pr_review_comment",
            "title": "Priya review on PR #38: In-memory cache cannot scale across replicas",
            "url_format_ok": true
          }
        ],
        "evidence_assessment": {
          "label": "contradicted"
        },
        "explanation": "Artifact 'src/cache/store.py' is governed primarily by accepted decision 'Migrate from In-Memory LRU to Distributed Redis Cluster', established by priya_patel on 2026-02-06.\n\nKey Rationale: ADR 0009: Decommission local in-memory dict and migrate to Redis cluster to prevent container OOMs and maintain cache consistency across autoscaled pods.\n\nEvolutionary History: This artifact progressed through 2 recorded decision milestones, including prior iterations or superseded proposals.",
        "indirect_support": [],
        "lifecycle_state": "accepted",
        "missing_corroboration": [
          "no outcome/test evidence linked"
        ],
        "needs_review": true,
        "statements": [
          {
            "event_id": "evt_adr_cache_0009",
            "flagged_unsupported": true,
            "overlap_ratio": 0.33,
            "passage": "PR #38 attempted local memory capping but was rejected because container autoscaling requires shared cache state.",
            "source_link": "https://github.com/acme-eng/distributed-cache-service/blob/main/docs/adr/0009-redis-cluster-cache.md",
            "supported": false,
            "text": "Artifact 'src/cache/store.py' is governed primarily by accepted decision 'Migrate from In-Memory LRU to Distributed Redis Cluster', established by priya_patel on 2026-02-06."
          },
          {
            "event_id": "evt_adr_cache_0009",
            "flagged_unsupported": true,
            "overlap_ratio": 0.39,
            "passage": "PR #38 attempted local memory capping but was rejected because container autoscaling requires shared cache state.",
            "source_link": "https://github.com/acme-eng/distributed-cache-service/blob/main/docs/adr/0009-redis-cluster-cache.md",
            "supported": false,
            "text": "Key Rationale: ADR 0009: Decommission local in-memory dict and migrate to Redis cluster to prevent container OOMs and maintain cache consistency across autoscaled pods."
          },
          {
            "event_id": null,
            "flagged_unsupported": true,
            "overlap_ratio": 0.0,
            "passage": null,
            "source_link": null,
            "supported": false,
            "text": "Evolutionary History: This artifact progressed through 2 recorded decision milestones, including prior iterations or superseded proposals."
          }
        ],
        "status": "grounded",
        "unsupported_sentences": [
          "Artifact 'src/cache/store.py' is governed primarily by accepted decision 'Migrate from In-Memory LRU to Distributed Redis Cluster', established by priya_patel on 2026-02-06.",
          "Key Rationale: ADR 0009: Decommission local in-memory dict and migrate to Redis cluster to prevent container OOMs and maintain cache consistency across autoscaled pods.",
          "Evolutionary History: This artifact progressed through 2 recorded decision milestones, including prior iterations or superseded proposals."
        ]
      },
      "status": "success"
    },
    "src/cache/store.py::cache_get": {
      "data": {
        "artifact": "src/cache/store.py::cache_get",
        "chain": [
          {
            "conflicting_evidence": [
              {
                "decision_id": "dec_cache_redis_accepted",
                "made_at": "2026-02-06T15:00:00Z",
                "state": "accepted",
                "title": "Migrate from In-Memory LRU to Distributed Redis Cluster",
                "type": "related_decision_on_entity"
              }
            ],
            "decision": {
              "decision_id": "dec_cache_local_lru_proposed",
              "made_at": "2026-02-03T14:30:00Z",
              "made_by": "marcus_vance",
              "rationale": "Keep cache strictly inside Python heap to guarantee sub-millisecond access and avoid external Redis infra.",
              "repo": "acme-eng/distributed-cache-service",
              "title": "Retain In-Memory LRU Cache with Process Memory Cap"
            },
            "decision_id": "dec_cache_local_lru_proposed",
            "direct_support": [
              {
                "author": "marcus_vance",
                "date": "2026-02-03T14:30:00Z",
                "event_id": "evt_pr_cache_38",
                "passage_end": 203,
                "passage_start": 155,
                "relation": "direct",
                "relevant_passage": "Keeps caching local with sub-millisecond access.",
                "source_group": "thread:acme-eng/distributed-cache-service#38",
                "source_link": "https://github.com/acme-eng/distributed-cache-service/pull/38",
                "source_type": "github_pr",
                "title": "PR #38: Add soft memory cap to in-memory LRU cache (Closes #34)",
                "url_format_ok": true
              }
            ],
            "evidence_assessment": {
              "label": "weak"
            },
            "indirect_support": [
              {
                "author": "marcus_vance",
                "date": "2026-02-03T14:30:00Z",
                "event_id": "evt_pr_cache_38",
                "passage_end": null,
                "passage_start": null,
                "relation": "indirect",
                "relevant_passage": null,
                "source_group": "thread:acme-eng/distributed-cache-service#38",
                "source_link": "https://github.com/acme-eng/distributed-cache-service/pull/38",
                "source_type": "github_pr",
                "title": "PR #38: Add soft memory cap to in-memory LRU cache (Closes #34)",
                "url_format_ok": true
              }
            ],
            "lifecycle_state": "superseded",
            "made_at": "2026-02-03T14:30:00Z",
            "made_by": "marcus_vance",
            "missing_corroboration": [
              "no independent corroborating source recorded (single source group)",
              "no outcome/test evidence linked"
            ],
            "needs_review": true,
            "rationale": "Keep cache strictly inside Python heap to guarantee sub-millisecond access and avoid external Redis infra.",
            "state": "superseded",
            "step_number": 1,
            "summary": "[SUPERSEDED] Retain In-Memory LRU Cache with Process Memory Cap (by marcus_vance on 2026-02-03)",
            "title": "Retain In-Memory LRU Cache with Process Memory Cap"
          },
          {
            "conflicting_evidence": [
              {
                "event_id": "evt_rev_cache_c201",
                "passage_text": "Priya review on PR #38: In-memory cache cannot scale across replicas",
                "relation": "contradicting",
                "source_group": "thread:acme-eng/distributed-cache-service#38",
                "type": "contradicting_passage"
              },
              {
                "decision_id": "dec_cache_local_lru_proposed",
                "made_at": "2026-02-03T14:30:00Z",
                "state": "superseded",
                "title": "Retain In-Memory LRU Cache with Process Memory Cap",
                "type": "related_decision_on_entity"
              }
            ],
            "decision": {
              "decision_id": "dec_cache_redis_accepted",
              "made_at": "2026-02-06T15:00:00Z",
              "made_by": "priya_patel",
              "rationale": "ADR 0009: Decommission local in-memory dict and migrate to Redis cluster to prevent container OOMs and maintain cache consistency across autoscaled pods.",
              "repo": "acme-eng/distributed-cache-service",
              "title": "Migrate from In-Memory LRU to Distributed Redis Cluster"
            },
            "decision_id": "dec_cache_redis_accepted",
            "direct_support": [
              {
                "author": "priya_patel",
                "date": "2026-02-06T15:00:00Z",
                "event_id": "evt_adr_cache_0009",
                "passage_end": 282,
                "passage_start": 169,
                "relation": "direct",
                "relevant_passage": "PR #38 attempted local memory capping but was rejected because container autoscaling requires shared cache state.",
                "source_group": "doc:acme-eng/distributed-cache-service:docs/adr/0009-redis-cluster-cache.md",
                "source_link": "https://github.com/acme-eng/distributed-cache-service/blob/main/docs/adr/0009-redis-cluster-cache.md",
                "source_type": "adr",
                "title": "ADR 0009: Migrate to Redis Cluster for Distributed Caching",
                "url_format_ok": true
              },
              {
                "author": "priya_patel",
                "date": "2026-02-06T15:00:00Z",
                "event_id": "evt_adr_cache_0009",
                "passage_end": 58,
                "passage_start": 0,
                "relation": "direct",
                "relevant_passage": "ADR 0009: Migrate to Redis Cluster for Distributed Caching",
                "source_group": "doc:acme-eng/distributed-cache-service:docs/adr/0009-redis-cluster-cache.md",
                "source_link": "https://github.com/acme-eng/distributed-cache-service/blob/main/docs/adr/0009-redis-cluster-cache.md",
                "source_type": "adr",
                "title": "ADR 0009: Migrate to Redis Cluster for Distributed Caching",
                "url_format_ok": true
              },
              {
                "author": "priya_patel",
                "date": "2026-02-04T09:00:00Z",
                "event_id": "evt_rev_cache_c201",
                "passage_end": 220,
                "passage_start": 184,
                "relation": "direct",
                "relevant_passage": "We need a distributed Redis cluster.",
                "source_group": "thread:acme-eng/distributed-cache-service#38",
                "source_link": "https://github.com/acme-eng/distributed-cache-service/pull/38#discussion_r201",
                "source_type": "pr_review_comment",
                "title": "Priya review on PR #38: In-memory cache cannot scale across replicas",
                "url_format_ok": true
              }
            ],
            "evidence_assessment": {
              "label": "contradicted"
            },
            "indirect_support": [],
            "lifecycle_state": "accepted",
            "made_at": "2026-02-06T15:00:00Z",
            "made_by": "priya_patel",
            "missing_corroboration": [
              "no outcome/test evidence linked"
            ],
            "needs_review": true,
            "rationale": "ADR 0009: Decommission local in-memory dict and migrate to Redis cluster to prevent container OOMs and maintain cache consistency across autoscaled pods.",
            "state": "accepted",
            "step_number": 2,
            "summary": "[ACCEPTED] Migrate from In-Memory LRU to Distributed Redis Cluster (by priya_patel on 2026-02-06)",
            "title": "Migrate from In-Memory LRU to Distributed Redis Cluster"
          }
        ],
        "citations": [
          {
            "author": "marcus_vance",
            "passage": "Keeps caching local with sub-millisecond access.",
            "relation": "direct",
            "source_id": "evt_pr_cache_38",
            "source_type": "github_pr",
            "source_url": "https://github.com/acme-eng/distributed-cache-service/pull/38",
            "timestamp": "2026-02-03T14:30:00Z",
            "title": "PR #38: Add soft memory cap to in-memory LRU cache (Closes #34)"
          },
          {
            "author": "priya_patel",
            "passage": "PR #38 attempted local memory capping but was rejected because container autoscaling requires shared cache state.",
            "relation": "direct",
            "source_id": "evt_adr_cache_0009",
            "source_type": "adr",
            "source_url": "https://github.com/acme-eng/distributed-cache-service/blob/main/docs/adr/0009-redis-cluster-cache.md",
            "timestamp": "2026-02-06T15:00:00Z",
            "title": "ADR 0009: Migrate to Redis Cluster for Distributed Caching"
          },
          {
            "author": "priya_patel",
            "passage": "ADR 0009: Migrate to Redis Cluster for Distributed Caching",
            "relation": "direct",
            "source_id": "evt_adr_cache_0009",
            "source_type": "adr",
            "source_url": "https://github.com/acme-eng/distributed-cache-service/blob/main/docs/adr/0009-redis-cluster-cache.md",
            "timestamp": "2026-02-06T15:00:00Z",
            "title": "ADR 0009: Migrate to Redis Cluster for Distributed Caching"
          },
          {
            "author": "priya_patel",
            "passage": "We need a distributed Redis cluster.",
            "relation": "direct",
            "source_id": "evt_rev_cache_c201",
            "source_type": "pr_review_comment",
            "source_url": "https://github.com/acme-eng/distributed-cache-service/pull/38#discussion_r201",
            "timestamp": "2026-02-04T09:00:00Z",
            "title": "Priya review on PR #38: In-memory cache cannot scale across replicas"
          }
        ],
        "claim_support_rate": 0.0,
        "conflicting_evidence": [
          {
            "event_id": "evt_rev_cache_c201",
            "passage_text": "Priya review on PR #38: In-memory cache cannot scale across replicas",
            "relation": "contradicting",
            "source_group": "thread:acme-eng/distributed-cache-service#38",
            "type": "contradicting_passage"
          },
          {
            "decision_id": "dec_cache_local_lru_proposed",
            "made_at": "2026-02-03T14:30:00Z",
            "state": "superseded",
            "title": "Retain In-Memory LRU Cache with Process Memory Cap",
            "type": "related_decision_on_entity"
          }
        ],
        "current_decision": "Migrate from In-Memory LRU to Distributed Redis Cluster",
        "current_state": "accepted",
        "decision": {
          "decision_id": "dec_cache_redis_accepted",
          "made_at": "2026-02-06T15:00:00Z",
          "made_by": "priya_patel",
          "rationale": "ADR 0009: Decommission local in-memory dict and migrate to Redis cluster to prevent container OOMs and maintain cache consistency across autoscaled pods.",
          "repo": "acme-eng/distributed-cache-service",
          "title": "Migrate from In-Memory LRU to Distributed Redis Cluster"
        },
        "direct_support": [
          {
            "author": "priya_patel",
            "date": "2026-02-06T15:00:00Z",
            "event_id": "evt_adr_cache_0009",
            "passage_end": 282,
            "passage_start": 169,
            "relation": "direct",
            "relevant_passage": "PR #38 attempted local memory capping but was rejected because container autoscaling requires shared cache state.",
            "source_group": "doc:acme-eng/distributed-cache-service:docs/adr/0009-redis-cluster-cache.md",
            "source_link": "https://github.com/acme-eng/distributed-cache-service/blob/main/docs/adr/0009-redis-cluster-cache.md",
            "source_type": "adr",
            "title": "ADR 0009: Migrate to Redis Cluster for Distributed Caching",
            "url_format_ok": true
          },
          {
            "author": "priya_patel",
            "date": "2026-02-06T15:00:00Z",
            "event_id": "evt_adr_cache_0009",
            "passage_end": 58,
            "passage_start": 0,
            "relation": "direct",
            "relevant_passage": "ADR 0009: Migrate to Redis Cluster for Distributed Caching",
            "source_group": "doc:acme-eng/distributed-cache-service:docs/adr/0009-redis-cluster-cache.md",
            "source_link": "https://github.com/acme-eng/distributed-cache-service/blob/main/docs/adr/0009-redis-cluster-cache.md",
            "source_type": "adr",
            "title": "ADR 0009: Migrate to Redis Cluster for Distributed Caching",
            "url_format_ok": true
          },
          {
            "author": "priya_patel",
            "date": "2026-02-04T09:00:00Z",
            "event_id": "evt_rev_cache_c201",
            "passage_end": 220,
            "passage_start": 184,
            "relation": "direct",
            "relevant_passage": "We need a distributed Redis cluster.",
            "source_group": "thread:acme-eng/distributed-cache-service#38",
            "source_link": "https://github.com/acme-eng/distributed-cache-service/pull/38#discussion_r201",
            "source_type": "pr_review_comment",
            "title": "Priya review on PR #38: In-memory cache cannot scale across replicas",
            "url_format_ok": true
          }
        ],
        "evidence_assessment": {
          "label": "contradicted"
        },
        "explanation": "Artifact 'src/cache/store.py::cache_get' is governed primarily by accepted decision 'Migrate from In-Memory LRU to Distributed Redis Cluster', established by priya_patel on 2026-02-06.\n\nKey Rationale: ADR 0009: Decommission local in-memory dict and migrate to Redis cluster to prevent container OOMs and maintain cache consistency across autoscaled pods.\n\nEvolutionary History: This artifact progressed through 2 recorded decision milestones, including prior iterations or superseded proposals.",
        "indirect_support": [],
        "lifecycle_state": "accepted",
        "missing_corroboration": [
          "no outcome/test evidence linked"
        ],
        "needs_review": true,
        "statements": [
          {
            "event_id": "evt_adr_cache_0009",
            "flagged_unsupported": true,
            "overlap_ratio": 0.31,
            "passage": "PR #38 attempted local memory capping but was rejected because container autoscaling requires shared cache state.",
            "source_link": "https://github.com/acme-eng/distributed-cache-service/blob/main/docs/adr/0009-redis-cluster-cache.md",
            "supported": false,
            "text": "Artifact 'src/cache/store.py::cache_get' is governed primarily by accepted decision 'Migrate from In-Memory LRU to Distributed Redis Cluster', established by priya_patel on 2026-02-06."
          },
          {
            "event_id": "evt_adr_cache_0009",
            "flagged_unsupported": true,
            "overlap_ratio": 0.39,
            "passage": "PR #38 attempted local memory capping but was rejected because container autoscaling requires shared cache state.",
            "source_link": "https://github.com/acme-eng/distributed-cache-service/blob/main/docs/adr/0009-redis-cluster-cache.md",
            "supported": false,
            "text": "Key Rationale: ADR 0009: Decommission local in-memory dict and migrate to Redis cluster to prevent container OOMs and maintain cache consistency across autoscaled pods."
          },
          {
            "event_id": null,
            "flagged_unsupported": true,
            "overlap_ratio": 0.0,
            "passage": null,
            "source_link": null,
            "supported": false,
            "text": "Evolutionary History: This artifact progressed through 2 recorded decision milestones, including prior iterations or superseded proposals."
          }
        ],
        "status": "grounded",
        "unsupported_sentences": [
          "Artifact 'src/cache/store.py::cache_get' is governed primarily by accepted decision 'Migrate from In-Memory LRU to Distributed Redis Cluster', established by priya_patel on 2026-02-06.",
          "Key Rationale: ADR 0009: Decommission local in-memory dict and migrate to Redis cluster to prevent container OOMs and maintain cache consistency across autoscaled pods.",
          "Evolutionary History: This artifact progressed through 2 recorded decision milestones, including prior iterations or superseded proposals."
        ]
      },
      "status": "success"
    },
    "src/cache/store.py::cache_set": {
      "data": {
        "artifact": "src/cache/store.py::cache_set",
        "chain": [
          {
            "conflicting_evidence": [
              {
                "decision_id": "dec_cache_redis_accepted",
                "made_at": "2026-02-06T15:00:00Z",
                "state": "accepted",
                "title": "Migrate from In-Memory LRU to Distributed Redis Cluster",
                "type": "related_decision_on_entity"
              }
            ],
            "decision": {
              "decision_id": "dec_cache_local_lru_proposed",
              "made_at": "2026-02-03T14:30:00Z",
              "made_by": "marcus_vance",
              "rationale": "Keep cache strictly inside Python heap to guarantee sub-millisecond access and avoid external Redis infra.",
              "repo": "acme-eng/distributed-cache-service",
              "title": "Retain In-Memory LRU Cache with Process Memory Cap"
            },
            "decision_id": "dec_cache_local_lru_proposed",
            "direct_support": [
              {
                "author": "marcus_vance",
                "date": "2026-02-03T14:30:00Z",
                "event_id": "evt_pr_cache_38",
                "passage_end": 203,
                "passage_start": 155,
                "relation": "direct",
                "relevant_passage": "Keeps caching local with sub-millisecond access.",
                "source_group": "thread:acme-eng/distributed-cache-service#38",
                "source_link": "https://github.com/acme-eng/distributed-cache-service/pull/38",
                "source_type": "github_pr",
                "title": "PR #38: Add soft memory cap to in-memory LRU cache (Closes #34)",
                "url_format_ok": true
              }
            ],
            "evidence_assessment": {
              "label": "weak"
            },
            "indirect_support": [
              {
                "author": "marcus_vance",
                "date": "2026-02-03T14:30:00Z",
                "event_id": "evt_pr_cache_38",
                "passage_end": null,
                "passage_start": null,
                "relation": "indirect",
                "relevant_passage": null,
                "source_group": "thread:acme-eng/distributed-cache-service#38",
                "source_link": "https://github.com/acme-eng/distributed-cache-service/pull/38",
                "source_type": "github_pr",
                "title": "PR #38: Add soft memory cap to in-memory LRU cache (Closes #34)",
                "url_format_ok": true
              }
            ],
            "lifecycle_state": "superseded",
            "made_at": "2026-02-03T14:30:00Z",
            "made_by": "marcus_vance",
            "missing_corroboration": [
              "no independent corroborating source recorded (single source group)",
              "no outcome/test evidence linked"
            ],
            "needs_review": true,
            "rationale": "Keep cache strictly inside Python heap to guarantee sub-millisecond access and avoid external Redis infra.",
            "state": "superseded",
            "step_number": 1,
            "summary": "[SUPERSEDED] Retain In-Memory LRU Cache with Process Memory Cap (by marcus_vance on 2026-02-03)",
            "title": "Retain In-Memory LRU Cache with Process Memory Cap"
          },
          {
            "conflicting_evidence": [
              {
                "event_id": "evt_rev_cache_c201",
                "passage_text": "Priya review on PR #38: In-memory cache cannot scale across replicas",
                "relation": "contradicting",
                "source_group": "thread:acme-eng/distributed-cache-service#38",
                "type": "contradicting_passage"
              },
              {
                "decision_id": "dec_cache_local_lru_proposed",
                "made_at": "2026-02-03T14:30:00Z",
                "state": "superseded",
                "title": "Retain In-Memory LRU Cache with Process Memory Cap",
                "type": "related_decision_on_entity"
              }
            ],
            "decision": {
              "decision_id": "dec_cache_redis_accepted",
              "made_at": "2026-02-06T15:00:00Z",
              "made_by": "priya_patel",
              "rationale": "ADR 0009: Decommission local in-memory dict and migrate to Redis cluster to prevent container OOMs and maintain cache consistency across autoscaled pods.",
              "repo": "acme-eng/distributed-cache-service",
              "title": "Migrate from In-Memory LRU to Distributed Redis Cluster"
            },
            "decision_id": "dec_cache_redis_accepted",
            "direct_support": [
              {
                "author": "priya_patel",
                "date": "2026-02-06T15:00:00Z",
                "event_id": "evt_adr_cache_0009",
                "passage_end": 282,
                "passage_start": 169,
                "relation": "direct",
                "relevant_passage": "PR #38 attempted local memory capping but was rejected because container autoscaling requires shared cache state.",
                "source_group": "doc:acme-eng/distributed-cache-service:docs/adr/0009-redis-cluster-cache.md",
                "source_link": "https://github.com/acme-eng/distributed-cache-service/blob/main/docs/adr/0009-redis-cluster-cache.md",
                "source_type": "adr",
                "title": "ADR 0009: Migrate to Redis Cluster for Distributed Caching",
                "url_format_ok": true
              },
              {
                "author": "priya_patel",
                "date": "2026-02-06T15:00:00Z",
                "event_id": "evt_adr_cache_0009",
                "passage_end": 58,
                "passage_start": 0,
                "relation": "direct",
                "relevant_passage": "ADR 0009: Migrate to Redis Cluster for Distributed Caching",
                "source_group": "doc:acme-eng/distributed-cache-service:docs/adr/0009-redis-cluster-cache.md",
                "source_link": "https://github.com/acme-eng/distributed-cache-service/blob/main/docs/adr/0009-redis-cluster-cache.md",
                "source_type": "adr",
                "title": "ADR 0009: Migrate to Redis Cluster for Distributed Caching",
                "url_format_ok": true
              },
              {
                "author": "priya_patel",
                "date": "2026-02-04T09:00:00Z",
                "event_id": "evt_rev_cache_c201",
                "passage_end": 220,
                "passage_start": 184,
                "relation": "direct",
                "relevant_passage": "We need a distributed Redis cluster.",
                "source_group": "thread:acme-eng/distributed-cache-service#38",
                "source_link": "https://github.com/acme-eng/distributed-cache-service/pull/38#discussion_r201",
                "source_type": "pr_review_comment",
                "title": "Priya review on PR #38: In-memory cache cannot scale across replicas",
                "url_format_ok": true
              }
            ],
            "evidence_assessment": {
              "label": "contradicted"
            },
            "indirect_support": [],
            "lifecycle_state": "accepted",
            "made_at": "2026-02-06T15:00:00Z",
            "made_by": "priya_patel",
            "missing_corroboration": [
              "no outcome/test evidence linked"
            ],
            "needs_review": true,
            "rationale": "ADR 0009: Decommission local in-memory dict and migrate to Redis cluster to prevent container OOMs and maintain cache consistency across autoscaled pods.",
            "state": "accepted",
            "step_number": 2,
            "summary": "[ACCEPTED] Migrate from In-Memory LRU to Distributed Redis Cluster (by priya_patel on 2026-02-06)",
            "title": "Migrate from In-Memory LRU to Distributed Redis Cluster"
          }
        ],
        "citations": [
          {
            "author": "marcus_vance",
            "passage": "Keeps caching local with sub-millisecond access.",
            "relation": "direct",
            "source_id": "evt_pr_cache_38",
            "source_type": "github_pr",
            "source_url": "https://github.com/acme-eng/distributed-cache-service/pull/38",
            "timestamp": "2026-02-03T14:30:00Z",
            "title": "PR #38: Add soft memory cap to in-memory LRU cache (Closes #34)"
          },
          {
            "author": "priya_patel",
            "passage": "PR #38 attempted local memory capping but was rejected because container autoscaling requires shared cache state.",
            "relation": "direct",
            "source_id": "evt_adr_cache_0009",
            "source_type": "adr",
            "source_url": "https://github.com/acme-eng/distributed-cache-service/blob/main/docs/adr/0009-redis-cluster-cache.md",
            "timestamp": "2026-02-06T15:00:00Z",
            "title": "ADR 0009: Migrate to Redis Cluster for Distributed Caching"
          },
          {
            "author": "priya_patel",
            "passage": "ADR 0009: Migrate to Redis Cluster for Distributed Caching",
            "relation": "direct",
            "source_id": "evt_adr_cache_0009",
            "source_type": "adr",
            "source_url": "https://github.com/acme-eng/distributed-cache-service/blob/main/docs/adr/0009-redis-cluster-cache.md",
            "timestamp": "2026-02-06T15:00:00Z",
            "title": "ADR 0009: Migrate to Redis Cluster for Distributed Caching"
          },
          {
            "author": "priya_patel",
            "passage": "We need a distributed Redis cluster.",
            "relation": "direct",
            "source_id": "evt_rev_cache_c201",
            "source_type": "pr_review_comment",
            "source_url": "https://github.com/acme-eng/distributed-cache-service/pull/38#discussion_r201",
            "timestamp": "2026-02-04T09:00:00Z",
            "title": "Priya review on PR #38: In-memory cache cannot scale across replicas"
          }
        ],
        "claim_support_rate": 0.0,
        "conflicting_evidence": [
          {
            "event_id": "evt_rev_cache_c201",
            "passage_text": "Priya review on PR #38: In-memory cache cannot scale across replicas",
            "relation": "contradicting",
            "source_group": "thread:acme-eng/distributed-cache-service#38",
            "type": "contradicting_passage"
          },
          {
            "decision_id": "dec_cache_local_lru_proposed",
            "made_at": "2026-02-03T14:30:00Z",
            "state": "superseded",
            "title": "Retain In-Memory LRU Cache with Process Memory Cap",
            "type": "related_decision_on_entity"
          }
        ],
        "current_decision": "Migrate from In-Memory LRU to Distributed Redis Cluster",
        "current_state": "accepted",
        "decision": {
          "decision_id": "dec_cache_redis_accepted",
          "made_at": "2026-02-06T15:00:00Z",
          "made_by": "priya_patel",
          "rationale": "ADR 0009: Decommission local in-memory dict and migrate to Redis cluster to prevent container OOMs and maintain cache consistency across autoscaled pods.",
          "repo": "acme-eng/distributed-cache-service",
          "title": "Migrate from In-Memory LRU to Distributed Redis Cluster"
        },
        "direct_support": [
          {
            "author": "priya_patel",
            "date": "2026-02-06T15:00:00Z",
            "event_id": "evt_adr_cache_0009",
            "passage_end": 282,
            "passage_start": 169,
            "relation": "direct",
            "relevant_passage": "PR #38 attempted local memory capping but was rejected because container autoscaling requires shared cache state.",
            "source_group": "doc:acme-eng/distributed-cache-service:docs/adr/0009-redis-cluster-cache.md",
            "source_link": "https://github.com/acme-eng/distributed-cache-service/blob/main/docs/adr/0009-redis-cluster-cache.md",
            "source_type": "adr",
            "title": "ADR 0009: Migrate to Redis Cluster for Distributed Caching",
            "url_format_ok": true
          },
          {
            "author": "priya_patel",
            "date": "2026-02-06T15:00:00Z",
            "event_id": "evt_adr_cache_0009",
            "passage_end": 58,
            "passage_start": 0,
            "relation": "direct",
            "relevant_passage": "ADR 0009: Migrate to Redis Cluster for Distributed Caching",
            "source_group": "doc:acme-eng/distributed-cache-service:docs/adr/0009-redis-cluster-cache.md",
            "source_link": "https://github.com/acme-eng/distributed-cache-service/blob/main/docs/adr/0009-redis-cluster-cache.md",
            "source_type": "adr",
            "title": "ADR 0009: Migrate to Redis Cluster for Distributed Caching",
            "url_format_ok": true
          },
          {
            "author": "priya_patel",
            "date": "2026-02-04T09:00:00Z",
            "event_id": "evt_rev_cache_c201",
            "passage_end": 220,
            "passage_start": 184,
            "relation": "direct",
            "relevant_passage": "We need a distributed Redis cluster.",
            "source_group": "thread:acme-eng/distributed-cache-service#38",
            "source_link": "https://github.com/acme-eng/distributed-cache-service/pull/38#discussion_r201",
            "source_type": "pr_review_comment",
            "title": "Priya review on PR #38: In-memory cache cannot scale across replicas",
            "url_format_ok": true
          }
        ],
        "evidence_assessment": {
          "label": "contradicted"
        },
        "explanation": "Artifact 'src/cache/store.py::cache_set' is governed primarily by accepted decision 'Migrate from In-Memory LRU to Distributed Redis Cluster', established by priya_patel on 2026-02-06.\n\nKey Rationale: ADR 0009: Decommission local in-memory dict and migrate to Redis cluster to prevent container OOMs and maintain cache consistency across autoscaled pods.\n\nEvolutionary History: This artifact progressed through 2 recorded decision milestones, including prior iterations or superseded proposals.",
        "indirect_support": [],
        "lifecycle_state": "accepted",
        "missing_corroboration": [
          "no outcome/test evidence linked"
        ],
        "needs_review": true,
        "statements": [
          {
            "event_id": "evt_adr_cache_0009",
            "flagged_unsupported": true,
            "overlap_ratio": 0.31,
            "passage": "PR #38 attempted local memory capping but was rejected because container autoscaling requires shared cache state.",
            "source_link": "https://github.com/acme-eng/distributed-cache-service/blob/main/docs/adr/0009-redis-cluster-cache.md",
            "supported": false,
            "text": "Artifact 'src/cache/store.py::cache_set' is governed primarily by accepted decision 'Migrate from In-Memory LRU to Distributed Redis Cluster', established by priya_patel on 2026-02-06."
          },
          {
            "event_id": "evt_adr_cache_0009",
            "flagged_unsupported": true,
            "overlap_ratio": 0.39,
            "passage": "PR #38 attempted local memory capping but was rejected because container autoscaling requires shared cache state.",
            "source_link": "https://github.com/acme-eng/distributed-cache-service/blob/main/docs/adr/0009-redis-cluster-cache.md",
            "supported": false,
            "text": "Key Rationale: ADR 0009: Decommission local in-memory dict and migrate to Redis cluster to prevent container OOMs and maintain cache consistency across autoscaled pods."
          },
          {
            "event_id": null,
            "flagged_unsupported": true,
            "overlap_ratio": 0.0,
            "passage": null,
            "source_link": null,
            "supported": false,
            "text": "Evolutionary History: This artifact progressed through 2 recorded decision milestones, including prior iterations or superseded proposals."
          }
        ],
        "status": "grounded",
        "unsupported_sentences": [
          "Artifact 'src/cache/store.py::cache_set' is governed primarily by accepted decision 'Migrate from In-Memory LRU to Distributed Redis Cluster', established by priya_patel on 2026-02-06.",
          "Key Rationale: ADR 0009: Decommission local in-memory dict and migrate to Redis cluster to prevent container OOMs and maintain cache consistency across autoscaled pods.",
          "Evolutionary History: This artifact progressed through 2 recorded decision milestones, including prior iterations or superseded proposals."
        ]
      },
      "status": "success"
    },
    "src/thermal/control.py": {
      "data": {
        "artifact": "src/thermal/control.py",
        "chain": [
          {
            "conflicting_evidence": [
              {
                "decision_id": "dec_thermal_pid_accepted",
                "made_at": "2026-01-15T16:00:00Z",
                "state": "accepted",
                "title": "Adopt Discrete PID Controller for Chamber Temperature Regulation",
                "type": "related_decision_on_entity"
              }
            ],
            "decision": {
              "decision_id": "dec_thermal_deadband_rejected",
              "made_at": "2026-01-12T15:00:00Z",
              "made_by": "sarah_chen",
              "rationale": "Tested in simulation following Issue #12; deadband was insufficient to prevent emergency chamber thermal trip.",
              "repo": "acme-eng/thermal-control-system",
              "title": "Reject Simple Deadband Hysteresis for Thermal Control"
            },
            "decision_id": "dec_thermal_deadband_rejected",
            "direct_support": [
              {
                "author": "marcus_vance",
                "date": "2026-01-11T11:20:00Z",
                "event_id": "evt_rev_thermal_comm1",
                "passage_end": 130,
                "passage_start": 127,
                "relation": "direct",
                "relevant_passage": "5C.",
                "source_group": "thread:acme-eng/thermal-control-system#12",
                "source_link": "https://github.com/acme-eng/thermal-control-system/issues/12#issuecomment-101",
                "source_type": "pr_review_comment",
                "title": "Marcus on Issue #12: Proposed deadband tuning",
                "url_format_ok": true
              },
              {
                "author": "sarah_chen",
                "date": "2026-01-12T14:45:00Z",
                "event_id": "evt_rev_thermal_comm2",
                "passage_end": 196,
                "passage_start": 156,
                "relation": "direct",
                "relevant_passage": "2C overshoot on rapid thermal transient.",
                "source_group": "thread:acme-eng/thermal-control-system#12",
                "source_link": "https://github.com/acme-eng/thermal-control-system/issues/12#issuecomment-102",
                "source_type": "pr_review_comment",
                "title": "Sarah on Issue #12: Benchmark results against deadband tuning",
                "url_format_ok": true
              },
              {
                "author": "marcus_vance",
                "date": "2026-01-11T11:20:00Z",
                "event_id": "evt_rev_thermal_comm1",
                "passage_end": 45,
                "passage_start": 0,
                "relation": "direct",
                "relevant_passage": "Marcus on Issue #12: Proposed deadband tuning",
                "source_group": "thread:acme-eng/thermal-control-system#12",
                "source_link": "https://github.com/acme-eng/thermal-control-system/issues/12#issuecomment-101",
                "source_type": "pr_review_comment",
                "title": "Marcus on Issue #12: Proposed deadband tuning",
                "url_format_ok": true
              },
              {
                "author": "sarah_chen",
                "date": "2026-01-12T14:45:00Z",
                "event_id": "evt_rev_thermal_comm2",
                "passage_end": 106,
                "passage_start": 62,
                "relation": "direct",
                "relevant_passage": "I benchmarked deadband tuning in simulation.",
                "source_group": "thread:acme-eng/thermal-control-system#12",
                "source_link": "https://github.com/acme-eng/thermal-control-system/issues/12#issuecomment-102",
                "source_type": "pr_review_comment",
                "title": "Sarah on Issue #12: Benchmark results against deadband tuning",
                "url_format_ok": true
              }
            ],
            "evidence_assessment": {
              "label": "weak"
            },
            "indirect_support": [],
            "lifecycle_state": "rejected",
            "made_at": "2026-01-12T15:00:00Z",
            "made_by": "sarah_chen",
            "missing_corroboration": [
              "no independent corroborating source recorded (single source group)"
            ],
            "needs_review": true,
            "rationale": "Tested in simulation following Issue #12; deadband was insufficient to prevent emergency chamber thermal trip.",
            "state": "rejected",
            "step_number": 1,
            "summary": "[REJECTED] Reject Simple Deadband Hysteresis for Thermal Control (by sarah_chen on 2026-01-12)",
            "title": "Reject Simple Deadband Hysteresis for Thermal Control"
          },
          {
            "conflicting_evidence": [
              {
                "event_id": "evt_adr_thermal_0004",
                "passage_text": "Deadband tuning was tested and rejected because it increased control latency by 17% and failed transient tests.",
                "relation": "contradicting",
                "source_group": "doc:acme-eng/thermal-control-system:docs/adr/0004-pid-thermal-regulation.md",
                "type": "contradicting_passage"
              }
            ],
            "decision": {
              "decision_id": "dec_thermal_pid_accepted",
              "made_at": "2026-01-15T16:00:00Z",
              "made_by": "sarah_chen",
              "rationale": "ADR 0004: Continuous PID loop with anti-windup clamping guarantees stability within +/- 0.4C of setpoint under heavy duty cycle.",
              "repo": "acme-eng/thermal-control-system",
              "title": "Adopt Discrete PID Controller for Chamber Temperature Regulation"
            },
            "decision_id": "dec_thermal_pid_accepted",
            "direct_support": [
              {
                "author": "sarah_chen",
                "date": "2026-01-18T10:00:00Z",
                "event_id": "evt_git_thermal_a1b2c3d4",
                "passage_end": 135,
                "passage_start": 79,
                "relation": "direct",
                "relevant_passage": "Replaces on-off controller with discrete PID controller.",
                "source_group": "commit:a1b2c3d4e5f67890",
                "source_link": "https://github.com/acme-eng/thermal-control-system/commit/a1b2c3d4e5f67890",
                "source_type": "git_commit",
                "title": "feat(thermal): implement discrete PID controller with anti-windup (Closes #12)",
                "url_format_ok": true
              },
              {
                "author": "sarah_chen",
                "date": "2026-01-15T16:00:00Z",
                "event_id": "evt_adr_thermal_0004",
                "passage_end": 540,
                "passage_start": 525,
                "relation": "direct",
                "relevant_passage": "4C of setpoint.",
                "source_group": "doc:acme-eng/thermal-control-system:docs/adr/0004-pid-thermal-regulation.md",
                "source_link": "https://github.com/acme-eng/thermal-control-system/blob/main/docs/adr/0004-pid-thermal-regulation.md",
                "source_type": "adr",
                "title": "ADR 0004: Adopt Discrete PID Algorithm for Thermal Regulation",
                "url_format_ok": true
              },
              {
                "author": "sarah_chen",
                "date": "2026-01-18T10:00:00Z",
                "event_id": "evt_git_thermal_a1b2c3d4",
                "passage_end": 156,
                "passage_start": 136,
                "relation": "direct",
                "relevant_passage": "Implements ADR 0004.",
                "source_group": "commit:a1b2c3d4e5f67890",
                "source_link": "https://github.com/acme-eng/thermal-control-system/commit/a1b2c3d4e5f67890",
                "source_type": "git_commit",
                "title": "feat(thermal): implement discrete PID controller with anti-windup (Closes #12)",
                "url_format_ok": true
              }
            ],
            "evidence_assessment": {
              "label": "contradicted"
            },
            "indirect_support": [],
            "lifecycle_state": "accepted",
            "made_at": "2026-01-15T16:00:00Z",
            "made_by": "sarah_chen",
            "missing_corroboration": [],
            "needs_review": true,
            "rationale": "ADR 0004: Continuous PID loop with anti-windup clamping guarantees stability within +/- 0.4C of setpoint under heavy duty cycle.",
            "state": "accepted",
            "step_number": 2,
            "summary": "[ACCEPTED] Adopt Discrete PID Controller for Chamber Temperature Regulation (by sarah_chen on 2026-01-15)",
            "title": "Adopt Discrete PID Controller for Chamber Temperature Regulation"
          }
        ],
        "citations": [
          {
            "author": "marcus_vance",
            "passage": "5C.",
            "relation": "direct",
            "source_id": "evt_rev_thermal_comm1",
            "source_type": "pr_review_comment",
            "source_url": "https://github.com/acme-eng/thermal-control-system/issues/12#issuecomment-101",
            "timestamp": "2026-01-11T11:20:00Z",
            "title": "Marcus on Issue #12: Proposed deadband tuning"
          },
          {
            "author": "sarah_chen",
            "passage": "2C overshoot on rapid thermal transient.",
            "relation": "direct",
            "source_id": "evt_rev_thermal_comm2",
            "source_type": "pr_review_comment",
            "source_url": "https://github.com/acme-eng/thermal-control-system/issues/12#issuecomment-102",
            "timestamp": "2026-01-12T14:45:00Z",
            "title": "Sarah on Issue #12: Benchmark results against deadband tuning"
          },
          {
            "author": "marcus_vance",
            "passage": "Marcus on Issue #12: Proposed deadband tuning",
            "relation": "direct",
            "source_id": "evt_rev_thermal_comm1",
            "source_type": "pr_review_comment",
            "source_url": "https://github.com/acme-eng/thermal-control-system/issues/12#issuecomment-101",
            "timestamp": "2026-01-11T11:20:00Z",
            "title": "Marcus on Issue #12: Proposed deadband tuning"
          },
          {
            "author": "sarah_chen",
            "passage": "I benchmarked deadband tuning in simulation.",
            "relation": "direct",
            "source_id": "evt_rev_thermal_comm2",
            "source_type": "pr_review_comment",
            "source_url": "https://github.com/acme-eng/thermal-control-system/issues/12#issuecomment-102",
            "timestamp": "2026-01-12T14:45:00Z",
            "title": "Sarah on Issue #12: Benchmark results against deadband tuning"
          },
          {
            "author": "sarah_chen",
            "passage": "Replaces on-off controller with discrete PID controller.",
            "relation": "direct",
            "source_id": "evt_git_thermal_a1b2c3d4",
            "source_type": "git_commit",
            "source_url": "https://github.com/acme-eng/thermal-control-system/commit/a1b2c3d4e5f67890",
            "timestamp": "2026-01-18T10:00:00Z",
            "title": "feat(thermal): implement discrete PID controller with anti-windup (Closes #12)"
          },
          {
            "author": "sarah_chen",
            "passage": "4C of setpoint.",
            "relation": "direct",
            "source_id": "evt_adr_thermal_0004",
            "source_type": "adr",
            "source_url": "https://github.com/acme-eng/thermal-control-system/blob/main/docs/adr/0004-pid-thermal-regulation.md",
            "timestamp": "2026-01-15T16:00:00Z",
            "title": "ADR 0004: Adopt Discrete PID Algorithm for Thermal Regulation"
          },
          {
            "author": "sarah_chen",
            "passage": "Implements ADR 0004.",
            "relation": "direct",
            "source_id": "evt_git_thermal_a1b2c3d4",
            "source_type": "git_commit",
            "source_url": "https://github.com/acme-eng/thermal-control-system/commit/a1b2c3d4e5f67890",
            "timestamp": "2026-01-18T10:00:00Z",
            "title": "feat(thermal): implement discrete PID controller with anti-windup (Closes #12)"
          }
        ],
        "claim_support_rate": 0.0,
        "conflicting_evidence": [
          {
            "event_id": "evt_adr_thermal_0004",
            "passage_text": "Deadband tuning was tested and rejected because it increased control latency by 17% and failed transient tests.",
            "relation": "contradicting",
            "source_group": "doc:acme-eng/thermal-control-system:docs/adr/0004-pid-thermal-regulation.md",
            "type": "contradicting_passage"
          }
        ],
        "current_decision": "Adopt Discrete PID Controller for Chamber Temperature Regulation",
        "current_state": "accepted",
        "decision": {
          "decision_id": "dec_thermal_pid_accepted",
          "made_at": "2026-01-15T16:00:00Z",
          "made_by": "sarah_chen",
          "rationale": "ADR 0004: Continuous PID loop with anti-windup clamping guarantees stability within +/- 0.4C of setpoint under heavy duty cycle.",
          "repo": "acme-eng/thermal-control-system",
          "title": "Adopt Discrete PID Controller for Chamber Temperature Regulation"
        },
        "direct_support": [
          {
            "author": "sarah_chen",
            "date": "2026-01-18T10:00:00Z",
            "event_id": "evt_git_thermal_a1b2c3d4",
            "passage_end": 135,
            "passage_start": 79,
            "relation": "direct",
            "relevant_passage": "Replaces on-off controller with discrete PID controller.",
            "source_group": "commit:a1b2c3d4e5f67890",
            "source_link": "https://github.com/acme-eng/thermal-control-system/commit/a1b2c3d4e5f67890",
            "source_type": "git_commit",
            "title": "feat(thermal): implement discrete PID controller with anti-windup (Closes #12)",
            "url_format_ok": true
          },
          {
            "author": "sarah_chen",
            "date": "2026-01-15T16:00:00Z",
            "event_id": "evt_adr_thermal_0004",
            "passage_end": 540,
            "passage_start": 525,
            "relation": "direct",
            "relevant_passage": "4C of setpoint.",
            "source_group": "doc:acme-eng/thermal-control-system:docs/adr/0004-pid-thermal-regulation.md",
            "source_link": "https://github.com/acme-eng/thermal-control-system/blob/main/docs/adr/0004-pid-thermal-regulation.md",
            "source_type": "adr",
            "title": "ADR 0004: Adopt Discrete PID Algorithm for Thermal Regulation",
            "url_format_ok": true
          },
          {
            "author": "sarah_chen",
            "date": "2026-01-18T10:00:00Z",
            "event_id": "evt_git_thermal_a1b2c3d4",
            "passage_end": 156,
            "passage_start": 136,
            "relation": "direct",
            "relevant_passage": "Implements ADR 0004.",
            "source_group": "commit:a1b2c3d4e5f67890",
            "source_link": "https://github.com/acme-eng/thermal-control-system/commit/a1b2c3d4e5f67890",
            "source_type": "git_commit",
            "title": "feat(thermal): implement discrete PID controller with anti-windup (Closes #12)",
            "url_format_ok": true
          }
        ],
        "evidence_assessment": {
          "label": "contradicted"
        },
        "explanation": "Artifact 'src/thermal/control.py' is governed primarily by accepted decision 'Adopt Discrete PID Controller for Chamber Temperature Regulation', established by sarah_chen on 2026-01-15.\n\nKey Rationale: ADR 0004: Continuous PID loop with anti-windup clamping guarantees stability within +/- 0.4C of setpoint under heavy duty cycle.\n\nEvolutionary History: This artifact progressed through 2 recorded decision milestones, including prior iterations or superseded proposals.",
        "indirect_support": [],
        "lifecycle_state": "accepted",
        "missing_corroboration": [],
        "needs_review": true,
        "statements": [
          {
            "event_id": "evt_adr_thermal_0004",
            "flagged_unsupported": true,
            "overlap_ratio": 0.25,
            "passage": "4C of setpoint.",
            "source_link": "https://github.com/acme-eng/thermal-control-system/blob/main/docs/adr/0004-pid-thermal-regulation.md",
            "supported": false,
            "text": "Artifact 'src/thermal/control.py' is governed primarily by accepted decision 'Adopt Discrete PID Controller for Chamber Temperature Regulation', established by sarah_chen on 2026-01-15."
          },
          {
            "event_id": "evt_adr_thermal_0004",
            "flagged_unsupported": true,
            "overlap_ratio": 0.15,
            "passage": "4C of setpoint.",
            "source_link": "https://github.com/acme-eng/thermal-control-system/blob/main/docs/adr/0004-pid-thermal-regulation.md",
            "supported": false,
            "text": "Key Rationale: ADR 0004: Continuous PID loop with anti-windup clamping guarantees stability within +/- 0.4C of setpoint under heavy duty cycle."
          },
          {
            "event_id": null,
            "flagged_unsupported": true,
            "overlap_ratio": 0.0,
            "passage": null,
            "source_link": null,
            "supported": false,
            "text": "Evolutionary History: This artifact progressed through 2 recorded decision milestones, including prior iterations or superseded proposals."
          }
        ],
        "status": "grounded",
        "unsupported_sentences": [
          "Artifact 'src/thermal/control.py' is governed primarily by accepted decision 'Adopt Discrete PID Controller for Chamber Temperature Regulation', established by sarah_chen on 2026-01-15.",
          "Key Rationale: ADR 0004: Continuous PID loop with anti-windup clamping guarantees stability within +/- 0.4C of setpoint under heavy duty cycle.",
          "Evolutionary History: This artifact progressed through 2 recorded decision milestones, including prior iterations or superseded proposals."
        ]
      },
      "status": "success"
    },
    "src/thermal/control.py::read_telemetry_sensor": {
      "data": {
        "artifact": "src/thermal/control.py::read_telemetry_sensor",
        "chain": [],
        "citations": [],
        "claim_support_rate": 0.0,
        "explanation": "No recorded architectural decisions found for artifact 'src/thermal/control.py::read_telemetry_sensor' in project history.",
        "statements": [],
        "status": "not_found",
        "unsupported_sentences": []
      },
      "status": "success"
    },
    "src/thermal/control.py::regulate_temperature": {
      "data": {
        "artifact": "src/thermal/control.py::regulate_temperature",
        "chain": [
          {
            "conflicting_evidence": [
              {
                "decision_id": "dec_thermal_pid_accepted",
                "made_at": "2026-01-15T16:00:00Z",
                "state": "accepted",
                "title": "Adopt Discrete PID Controller for Chamber Temperature Regulation",
                "type": "related_decision_on_entity"
              }
            ],
            "decision": {
              "decision_id": "dec_thermal_deadband_rejected",
              "made_at": "2026-01-12T15:00:00Z",
              "made_by": "sarah_chen",
              "rationale": "Tested in simulation following Issue #12; deadband was insufficient to prevent emergency chamber thermal trip.",
              "repo": "acme-eng/thermal-control-system",
              "title": "Reject Simple Deadband Hysteresis for Thermal Control"
            },
            "decision_id": "dec_thermal_deadband_rejected",
            "direct_support": [
              {
                "author": "marcus_vance",
                "date": "2026-01-11T11:20:00Z",
                "event_id": "evt_rev_thermal_comm1",
                "passage_end": 130,
                "passage_start": 127,
                "relation": "direct",
                "relevant_passage": "5C.",
                "source_group": "thread:acme-eng/thermal-control-system#12",
                "source_link": "https://github.com/acme-eng/thermal-control-system/issues/12#issuecomment-101",
                "source_type": "pr_review_comment",
                "title": "Marcus on Issue #12: Proposed deadband tuning",
                "url_format_ok": true
              },
              {
                "author": "sarah_chen",
                "date": "2026-01-12T14:45:00Z",
                "event_id": "evt_rev_thermal_comm2",
                "passage_end": 196,
                "passage_start": 156,
                "relation": "direct",
                "relevant_passage": "2C overshoot on rapid thermal transient.",
                "source_group": "thread:acme-eng/thermal-control-system#12",
                "source_link": "https://github.com/acme-eng/thermal-control-system/issues/12#issuecomment-102",
                "source_type": "pr_review_comment",
                "title": "Sarah on Issue #12: Benchmark results against deadband tuning",
                "url_format_ok": true
              },
              {
                "author": "marcus_vance",
                "date": "2026-01-11T11:20:00Z",
                "event_id": "evt_rev_thermal_comm1",
                "passage_end": 45,
                "passage_start": 0,
                "relation": "direct",
                "relevant_passage": "Marcus on Issue #12: Proposed deadband tuning",
                "source_group": "thread:acme-eng/thermal-control-system#12",
                "source_link": "https://github.com/acme-eng/thermal-control-system/issues/12#issuecomment-101",
                "source_type": "pr_review_comment",
                "title": "Marcus on Issue #12: Proposed deadband tuning",
                "url_format_ok": true
              },
              {
                "author": "sarah_chen",
                "date": "2026-01-12T14:45:00Z",
                "event_id": "evt_rev_thermal_comm2",
                "passage_end": 106,
                "passage_start": 62,
                "relation": "direct",
                "relevant_passage": "I benchmarked deadband tuning in simulation.",
                "source_group": "thread:acme-eng/thermal-control-system#12",
                "source_link": "https://github.com/acme-eng/thermal-control-system/issues/12#issuecomment-102",
                "source_type": "pr_review_comment",
                "title": "Sarah on Issue #12: Benchmark results against deadband tuning",
                "url_format_ok": true
              }
            ],
            "evidence_assessment": {
              "label": "weak"
            },
            "indirect_support": [],
            "lifecycle_state": "rejected",
            "made_at": "2026-01-12T15:00:00Z",
            "made_by": "sarah_chen",
            "missing_corroboration": [
              "no independent corroborating source recorded (single source group)"
            ],
            "needs_review": true,
            "rationale": "Tested in simulation following Issue #12; deadband was insufficient to prevent emergency chamber thermal trip.",
            "state": "rejected",
            "step_number": 1,
            "summary": "[REJECTED] Reject Simple Deadband Hysteresis for Thermal Control (by sarah_chen on 2026-01-12)",
            "title": "Reject Simple Deadband Hysteresis for Thermal Control"
          },
          {
            "conflicting_evidence": [
              {
                "event_id": "evt_adr_thermal_0004",
                "passage_text": "Deadband tuning was tested and rejected because it increased control latency by 17% and failed transient tests.",
                "relation": "contradicting",
                "source_group": "doc:acme-eng/thermal-control-system:docs/adr/0004-pid-thermal-regulation.md",
                "type": "contradicting_passage"
              }
            ],
            "decision": {
              "decision_id": "dec_thermal_pid_accepted",
              "made_at": "2026-01-15T16:00:00Z",
              "made_by": "sarah_chen",
              "rationale": "ADR 0004: Continuous PID loop with anti-windup clamping guarantees stability within +/- 0.4C of setpoint under heavy duty cycle.",
              "repo": "acme-eng/thermal-control-system",
              "title": "Adopt Discrete PID Controller for Chamber Temperature Regulation"
            },
            "decision_id": "dec_thermal_pid_accepted",
            "direct_support": [
              {
                "author": "sarah_chen",
                "date": "2026-01-18T10:00:00Z",
                "event_id": "evt_git_thermal_a1b2c3d4",
                "passage_end": 135,
                "passage_start": 79,
                "relation": "direct",
                "relevant_passage": "Replaces on-off controller with discrete PID controller.",
                "source_group": "commit:a1b2c3d4e5f67890",
                "source_link": "https://github.com/acme-eng/thermal-control-system/commit/a1b2c3d4e5f67890",
                "source_type": "git_commit",
                "title": "feat(thermal): implement discrete PID controller with anti-windup (Closes #12)",
                "url_format_ok": true
              },
              {
                "author": "sarah_chen",
                "date": "2026-01-15T16:00:00Z",
                "event_id": "evt_adr_thermal_0004",
                "passage_end": 540,
                "passage_start": 525,
                "relation": "direct",
                "relevant_passage": "4C of setpoint.",
                "source_group": "doc:acme-eng/thermal-control-system:docs/adr/0004-pid-thermal-regulation.md",
                "source_link": "https://github.com/acme-eng/thermal-control-system/blob/main/docs/adr/0004-pid-thermal-regulation.md",
                "source_type": "adr",
                "title": "ADR 0004: Adopt Discrete PID Algorithm for Thermal Regulation",
                "url_format_ok": true
              },
              {
                "author": "sarah_chen",
                "date": "2026-01-18T10:00:00Z",
                "event_id": "evt_git_thermal_a1b2c3d4",
                "passage_end": 156,
                "passage_start": 136,
                "relation": "direct",
                "relevant_passage": "Implements ADR 0004.",
                "source_group": "commit:a1b2c3d4e5f67890",
                "source_link": "https://github.com/acme-eng/thermal-control-system/commit/a1b2c3d4e5f67890",
                "source_type": "git_commit",
                "title": "feat(thermal): implement discrete PID controller with anti-windup (Closes #12)",
                "url_format_ok": true
              }
            ],
            "evidence_assessment": {
              "label": "contradicted"
            },
            "indirect_support": [],
            "lifecycle_state": "accepted",
            "made_at": "2026-01-15T16:00:00Z",
            "made_by": "sarah_chen",
            "missing_corroboration": [],
            "needs_review": true,
            "rationale": "ADR 0004: Continuous PID loop with anti-windup clamping guarantees stability within +/- 0.4C of setpoint under heavy duty cycle.",
            "state": "accepted",
            "step_number": 2,
            "summary": "[ACCEPTED] Adopt Discrete PID Controller for Chamber Temperature Regulation (by sarah_chen on 2026-01-15)",
            "title": "Adopt Discrete PID Controller for Chamber Temperature Regulation"
          }
        ],
        "citations": [
          {
            "author": "marcus_vance",
            "passage": "5C.",
            "relation": "direct",
            "source_id": "evt_rev_thermal_comm1",
            "source_type": "pr_review_comment",
            "source_url": "https://github.com/acme-eng/thermal-control-system/issues/12#issuecomment-101",
            "timestamp": "2026-01-11T11:20:00Z",
            "title": "Marcus on Issue #12: Proposed deadband tuning"
          },
          {
            "author": "sarah_chen",
            "passage": "2C overshoot on rapid thermal transient.",
            "relation": "direct",
            "source_id": "evt_rev_thermal_comm2",
            "source_type": "pr_review_comment",
            "source_url": "https://github.com/acme-eng/thermal-control-system/issues/12#issuecomment-102",
            "timestamp": "2026-01-12T14:45:00Z",
            "title": "Sarah on Issue #12: Benchmark results against deadband tuning"
          },
          {
            "author": "marcus_vance",
            "passage": "Marcus on Issue #12: Proposed deadband tuning",
            "relation": "direct",
            "source_id": "evt_rev_thermal_comm1",
            "source_type": "pr_review_comment",
            "source_url": "https://github.com/acme-eng/thermal-control-system/issues/12#issuecomment-101",
            "timestamp": "2026-01-11T11:20:00Z",
            "title": "Marcus on Issue #12: Proposed deadband tuning"
          },
          {
            "author": "sarah_chen",
            "passage": "I benchmarked deadband tuning in simulation.",
            "relation": "direct",
            "source_id": "evt_rev_thermal_comm2",
            "source_type": "pr_review_comment",
            "source_url": "https://github.com/acme-eng/thermal-control-system/issues/12#issuecomment-102",
            "timestamp": "2026-01-12T14:45:00Z",
            "title": "Sarah on Issue #12: Benchmark results against deadband tuning"
          },
          {
            "author": "sarah_chen",
            "passage": "Replaces on-off controller with discrete PID controller.",
            "relation": "direct",
            "source_id": "evt_git_thermal_a1b2c3d4",
            "source_type": "git_commit",
            "source_url": "https://github.com/acme-eng/thermal-control-system/commit/a1b2c3d4e5f67890",
            "timestamp": "2026-01-18T10:00:00Z",
            "title": "feat(thermal): implement discrete PID controller with anti-windup (Closes #12)"
          },
          {
            "author": "sarah_chen",
            "passage": "4C of setpoint.",
            "relation": "direct",
            "source_id": "evt_adr_thermal_0004",
            "source_type": "adr",
            "source_url": "https://github.com/acme-eng/thermal-control-system/blob/main/docs/adr/0004-pid-thermal-regulation.md",
            "timestamp": "2026-01-15T16:00:00Z",
            "title": "ADR 0004: Adopt Discrete PID Algorithm for Thermal Regulation"
          },
          {
            "author": "sarah_chen",
            "passage": "Implements ADR 0004.",
            "relation": "direct",
            "source_id": "evt_git_thermal_a1b2c3d4",
            "source_type": "git_commit",
            "source_url": "https://github.com/acme-eng/thermal-control-system/commit/a1b2c3d4e5f67890",
            "timestamp": "2026-01-18T10:00:00Z",
            "title": "feat(thermal): implement discrete PID controller with anti-windup (Closes #12)"
          }
        ],
        "claim_support_rate": 0.0,
        "conflicting_evidence": [
          {
            "event_id": "evt_adr_thermal_0004",
            "passage_text": "Deadband tuning was tested and rejected because it increased control latency by 17% and failed transient tests.",
            "relation": "contradicting",
            "source_group": "doc:acme-eng/thermal-control-system:docs/adr/0004-pid-thermal-regulation.md",
            "type": "contradicting_passage"
          }
        ],
        "current_decision": "Adopt Discrete PID Controller for Chamber Temperature Regulation",
        "current_state": "accepted",
        "decision": {
          "decision_id": "dec_thermal_pid_accepted",
          "made_at": "2026-01-15T16:00:00Z",
          "made_by": "sarah_chen",
          "rationale": "ADR 0004: Continuous PID loop with anti-windup clamping guarantees stability within +/- 0.4C of setpoint under heavy duty cycle.",
          "repo": "acme-eng/thermal-control-system",
          "title": "Adopt Discrete PID Controller for Chamber Temperature Regulation"
        },
        "direct_support": [
          {
            "author": "sarah_chen",
            "date": "2026-01-18T10:00:00Z",
            "event_id": "evt_git_thermal_a1b2c3d4",
            "passage_end": 135,
            "passage_start": 79,
            "relation": "direct",
            "relevant_passage": "Replaces on-off controller with discrete PID controller.",
            "source_group": "commit:a1b2c3d4e5f67890",
            "source_link": "https://github.com/acme-eng/thermal-control-system/commit/a1b2c3d4e5f67890",
            "source_type": "git_commit",
            "title": "feat(thermal): implement discrete PID controller with anti-windup (Closes #12)",
            "url_format_ok": true
          },
          {
            "author": "sarah_chen",
            "date": "2026-01-15T16:00:00Z",
            "event_id": "evt_adr_thermal_0004",
            "passage_end": 540,
            "passage_start": 525,
            "relation": "direct",
            "relevant_passage": "4C of setpoint.",
            "source_group": "doc:acme-eng/thermal-control-system:docs/adr/0004-pid-thermal-regulation.md",
            "source_link": "https://github.com/acme-eng/thermal-control-system/blob/main/docs/adr/0004-pid-thermal-regulation.md",
            "source_type": "adr",
            "title": "ADR 0004: Adopt Discrete PID Algorithm for Thermal Regulation",
            "url_format_ok": true
          },
          {
            "author": "sarah_chen",
            "date": "2026-01-18T10:00:00Z",
            "event_id": "evt_git_thermal_a1b2c3d4",
            "passage_end": 156,
            "passage_start": 136,
            "relation": "direct",
            "relevant_passage": "Implements ADR 0004.",
            "source_group": "commit:a1b2c3d4e5f67890",
            "source_link": "https://github.com/acme-eng/thermal-control-system/commit/a1b2c3d4e5f67890",
            "source_type": "git_commit",
            "title": "feat(thermal): implement discrete PID controller with anti-windup (Closes #12)",
            "url_format_ok": true
          }
        ],
        "evidence_assessment": {
          "label": "contradicted"
        },
        "explanation": "Artifact 'src/thermal/control.py::regulate_temperature' is governed primarily by accepted decision 'Adopt Discrete PID Controller for Chamber Temperature Regulation', established by sarah_chen on 2026-01-15.\n\nKey Rationale: ADR 0004: Continuous PID loop with anti-windup clamping guarantees stability within +/- 0.4C of setpoint under heavy duty cycle.\n\nEvolutionary History: This artifact progressed through 2 recorded decision milestones, including prior iterations or superseded proposals.",
        "indirect_support": [],
        "lifecycle_state": "accepted",
        "missing_corroboration": [],
        "needs_review": true,
        "statements": [
          {
            "event_id": "evt_adr_thermal_0004",
            "flagged_unsupported": true,
            "overlap_ratio": 0.24,
            "passage": "4C of setpoint.",
            "source_link": "https://github.com/acme-eng/thermal-control-system/blob/main/docs/adr/0004-pid-thermal-regulation.md",
            "supported": false,
            "text": "Artifact 'src/thermal/control.py::regulate_temperature' is governed primarily by accepted decision 'Adopt Discrete PID Controller for Chamber Temperature Regulation', established by sarah_chen on 2026-01-15."
          },
          {
            "event_id": "evt_adr_thermal_0004",
            "flagged_unsupported": true,
            "overlap_ratio": 0.15,
            "passage": "4C of setpoint.",
            "source_link": "https://github.com/acme-eng/thermal-control-system/blob/main/docs/adr/0004-pid-thermal-regulation.md",
            "supported": false,
            "text": "Key Rationale: ADR 0004: Continuous PID loop with anti-windup clamping guarantees stability within +/- 0.4C of setpoint under heavy duty cycle."
          },
          {
            "event_id": null,
            "flagged_unsupported": true,
            "overlap_ratio": 0.0,
            "passage": null,
            "source_link": null,
            "supported": false,
            "text": "Evolutionary History: This artifact progressed through 2 recorded decision milestones, including prior iterations or superseded proposals."
          }
        ],
        "status": "grounded",
        "unsupported_sentences": [
          "Artifact 'src/thermal/control.py::regulate_temperature' is governed primarily by accepted decision 'Adopt Discrete PID Controller for Chamber Temperature Regulation', established by sarah_chen on 2026-01-15.",
          "Key Rationale: ADR 0004: Continuous PID loop with anti-windup clamping guarantees stability within +/- 0.4C of setpoint under heavy duty cycle.",
          "Evolutionary History: This artifact progressed through 2 recorded decision milestones, including prior iterations or superseded proposals."
        ]
      },
      "status": "success"
    }
  },
  "generation_date": "2026-10-12T00:00:00Z"
};
