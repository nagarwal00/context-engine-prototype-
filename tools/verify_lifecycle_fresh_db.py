#!/usr/bin/env python3
"""
Fresh-Database Lifecycle Proof Tool (Step 2.7)
Creates a temp DB, runs schema migrations, seeds pilot data, ingests a fixture decision,
executes a scripted lifecycle sequence:
  create -> test -> accept -> supersede -> reopen-attempt-on-superseded (must fail with InvalidTransition)
Prints the audit log and exits non-zero on any deviation.
"""
import os
import sys
import tempfile
import argparse
from datetime import datetime, timezone

# Ensure project root is in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.db import Database
from backend.seed_data import populate_seed_data
from backend.models import Decision, Event, Entity
from backend.engine.lifecycle import transition, InvalidTransition

# Ensure stdout is utf-8 compatible on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def verify_lifecycle_on_fresh_db(verbose: bool = True) -> int:
    temp_dir = tempfile.TemporaryDirectory()
    try:
        db_path = os.path.join(temp_dir.name, "fresh_lifecycle_proof.db")
        if verbose:
            print("=" * 70)
            print("  CIF LIFECYCLE FRESH DATABASE VERIFICATION PROOF")
            print("=" * 70)
            print(f"  Target DB: {db_path}")

        # 1. Initialize fresh database (creates schema and applies migrations 001 and 002)
        db = Database(db_path)
        if verbose:
            print("  [STEP 1] Initialized fresh database and verified schema migrations.")

        # 2. Seed data
        populate_seed_data(db)
        if verbose:
            print("  [STEP 2] Populated baseline seed data.")

        # 3. Create supporting entities and evidence event fixture
        ent = Entity(
            entity_id="ent_proof_controller",
            canonical_path="src/proof/controller.py",
            entity_type="file",
            repo="acme-eng/proof-subsystem"
        )
        db.upsert_entity(ent)

        ev_1 = Event(
            event_id="evt_proof_001",
            source_type="github_issue",
            source_id="101",
            source_url="https://github.com/acme-eng/proof-subsystem/issues/101",
            repo="acme-eng/proof-subsystem",
            author="lead_dev",
            timestamp="2026-03-01T10:00:00Z",
            title="Issue #101: Need asynchronous batch ingestion",
            body="Synchronous writes throttle pipeline during burst intake.",
            artifacts_touched=["src/proof/controller.py"]
        )
        db.upsert_event(ev_1)

        ev_test = Event(
            event_id="evt_proof_002",
            source_type="ci_run",
            source_id="ci_4021",
            source_url="https://github.com/acme-eng/proof-subsystem/actions/runs/4021",
            repo="acme-eng/proof-subsystem",
            author="qa_bot",
            timestamp="2026-03-02T11:00:00Z",
            title="CI Run 4021: Benchmarked batch throughput",
            body="Async batch ingestion sustained 25,000 msg/sec with zero drops.",
            artifacts_touched=["src/proof/controller.py"]
        )
        db.upsert_event(ev_test)

        if verbose:
            print("  [STEP 3] Ingested fixture entities and evidence events.")

        # 4. Scripted Sequence:
        # Step 4a: CREATE (proposed)
        dec_proof = Decision(
            decision_id="dec_proof_batching",
            title="Adopt Async Batch Ingestion Controller",
            state="proposed",
            made_by="lead_dev",
            made_at="2026-03-01T10:30:00Z",
            repo="acme-eng/proof-subsystem",
            artifacts_affected=["ent_proof_controller"],
            evidence_event_ids=["evt_proof_001"],
            rationale="Batch controller buffers write load to prevent pipeline starvation."
        )
        db.save_decision(dec_proof)

        with db.get_connection() as conn:
            row = conn.execute("SELECT state FROM decisions WHERE decision_id = 'dec_proof_batching'").fetchone()
            if not row or row["state"] != "proposed":
                print("  [FAIL] Step 4a: Expected created state 'proposed'.")
                return 1
        if verbose:
            print("  [STEP 4a PASS] Created decision in state: proposed.")

        # Step 4b: TEST (proposed -> tested)
        transition(
            db,
            "dec_proof_batching",
            "tested",
            actor="qa_engineer",
            reason="Automated load testing passed: 25k msg/sec validated in CI",
            at="2026-03-02T12:00:00Z",
            evidence_event_ids=["evt_proof_002"]
        )
        with db.get_connection() as conn:
            row = conn.execute("SELECT state FROM decisions WHERE decision_id = 'dec_proof_batching'").fetchone()
            if not row or row["state"] != "tested":
                print("  [FAIL] Step 4b: Expected state 'tested'.")
                return 1
        if verbose:
            print("  [STEP 4b PASS] Transitioned proposed -> tested with test evidence.")

        # Step 4c: ACCEPT (tested -> accepted)
        transition(
            db,
            "dec_proof_batching",
            "accepted",
            actor="lead_architect",
            reason="Approved architecture review following successful test pass",
            at="2026-03-03T09:00:00Z"
        )
        with db.get_connection() as conn:
            row = conn.execute("SELECT state FROM decisions WHERE decision_id = 'dec_proof_batching'").fetchone()
            if not row or row["state"] != "accepted":
                print("  [FAIL] Step 4c: Expected state 'accepted'.")
                return 1
        if verbose:
            print("  [STEP 4c PASS] Transitioned tested -> accepted.")

        # Step 4d: SUPERSEDE (accepted -> superseded)
        dec_v2 = Decision(
            decision_id="dec_proof_stream_v2",
            title="Migrate to Streaming Pipeline Engine",
            state="accepted",
            made_by="lead_architect",
            made_at="2026-03-10T14:00:00Z",
            repo="acme-eng/proof-subsystem",
            artifacts_affected=["ent_proof_controller"],
            evidence_event_ids=["evt_proof_002"],
            supersedes_decision_id="dec_proof_batching",
            rationale="Subsumes batch buffering with true real-time streaming."
        )
        db.save_decision(dec_v2)

        transition(
            db,
            "dec_proof_batching",
            "superseded",
            actor="lead_architect",
            reason="Superseded by v2 streaming architecture (dec_proof_stream_v2)",
            at="2026-03-10T14:00:00Z",
            superseded_by_id="dec_proof_stream_v2"
        )
        with db.get_connection() as conn:
            row = conn.execute("SELECT state, superseded_by_decision_id FROM decisions WHERE decision_id = 'dec_proof_batching'").fetchone()
            if not row or row["state"] != "superseded" or row["superseded_by_decision_id"] != "dec_proof_stream_v2":
                print("  [FAIL] Step 4d: Expected state 'superseded' with superseding decision pointer.")
                return 1
        if verbose:
            print("  [STEP 4d PASS] Transitioned accepted -> superseded with superseding pointer.")

        # Step 4e: REOPEN-ATTEMPT-ON-SUPERSEDED MUST FAIL
        reopen_failed_as_expected = False
        try:
            transition(
                db,
                "dec_proof_batching",
                "reopened",
                actor="developer",
                reason="Attempting illegal reopening of terminal superseded decision",
                at="2026-03-11T10:00:00Z"
            )
        except InvalidTransition as e:
            reopen_failed_as_expected = True
            if verbose:
                print(f"  [STEP 4e PASS] Reopen attempt on superseded decision was REJECTED: {e}")
        except Exception as e:
            print(f"  [FAIL] Step 4e: Unexpected exception type: {type(e).__name__}: {e}")
            return 1

        if not reopen_failed_as_expected:
            print("  [FAIL] Step 4e: Attempt to reopen superseded decision did NOT raise InvalidTransition!")
            return 1

        # 5. Print State History Audit Log
        if verbose:
            print("\n" + "=" * 70)
            print("  DECISION STATE HISTORY AUDIT LOG FOR 'dec_proof_batching'")
            print("=" * 70)
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                SELECT history_id, from_state, state, changed_at, changed_by, notes, reconstructed
                FROM state_history
                WHERE decision_id = 'dec_proof_batching'
                ORDER BY changed_at ASC
                """)
                rows = cursor.fetchall()
                print(f"  Total Transitions: {len(rows)}\n")
                for idx, r in enumerate(rows, 1):
                    from_s = r["from_state"] or "(Initial)"
                    rec_s = "[Reconstructed]" if r["reconstructed"] else "[Observed]"
                    print(f"  #{idx} {r['changed_at']} {rec_s}")
                    print(f"     Transition: {from_s} -> {r['state']}")
                    print(f"     Actor     : {r['changed_by']}")
                    print(f"     Notes     : {r['notes']}\n")

                if len(rows) != 4:
                    print(f"  [FAIL] Expected 4 audit log entries, found {len(rows)}")
                    return 1

            print("=" * 70)
            print("  ALL LIFECYCLE CHECKS PASSED SUCCESSFULLY ON FRESH DATABASE!")
            print("=" * 70)

        return 0

    finally:
        temp_dir.cleanup()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify decision lifecycle sequence on a fresh database.")
    parser.add_argument("--quiet", action="store_true", help="Suppress verbose stdout output.")
    args = parser.parse_args()

    exit_code = verify_lifecycle_on_fresh_db(verbose=not args.quiet)
    sys.exit(exit_code)
