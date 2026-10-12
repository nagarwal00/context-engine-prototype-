"""
Decision Half-Life & Staleness Engine (Step 5.2)
Monitors machine-checkable assumptions for architectural decisions.
Decisions NEVER expire by age alone. Staleness is triggered ONLY by events
affecting an assumption (dependency upgrades, config changes, deleted files, manual flags).

Freshness state model: fresh -> stale -> under_review -> revalidated.
"""
import json
import re
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from backend.models import Event, Decision
from backend.db import Database


def parse_semver(v_str: str) -> Tuple[int, ...]:
    """Extracts numeric version tuple from version string (e.g. '2.4.1' -> (2, 4, 1))."""
    if not v_str:
        return (0,)
    matches = re.findall(r"\d+", v_str)
    return tuple(int(m) for m in matches) if matches else (0,)


def check_version_violation(installed_version: str, constraint: str, max_version: Optional[str] = None) -> bool:
    """
    Checks if installed_version violates a max_version or constraint.
    Returns True if the assumption is BROKEN (version upgraded beyond allowed).
    """
    installed = parse_semver(installed_version)
    if max_version:
        max_v = parse_semver(max_version)
        if installed >= max_v:
            return True

    if constraint:
        # e.g. "<2.0.0", "<=1.5", "==1.0"
        m = re.match(r"^([<>!=]=?)\s*([0-9.]+)", constraint.strip())
        if m:
            op, target_str = m.groups()
            target = parse_semver(target_str)
            if op == "<" and installed >= target:
                return True
            elif op == "<=" and installed > target:
                return True
            elif op in ("==", "=") and installed != target:
                return True
            elif op == "!=" and installed == target:
                return True

    return False


class StalenessEngine:
    def __init__(self, db: Database):
        self.db = db

    def add_assumption(
        self,
        decision_id: str,
        text: str,
        watch_type: str,
        watch_params: Dict[str, Any],
        status: str = "valid"
    ) -> str:
        """Registers a machine-checkable assumption for an architectural decision."""
        if watch_type not in ("dependency_version", "config_value", "file_exists", "infrastructure_note", "manual"):
            raise ValueError(f"Invalid watch_type: {watch_type}")

        assumption_id = f"assump_{decision_id}_{os.urandom(4).hex()}"
        with self.db.get_connection() as conn:
            conn.execute("""
            INSERT INTO decision_assumptions (
                assumption_id, decision_id, text, watch_type, watch_params_json, status, last_checked_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                assumption_id,
                decision_id,
                text,
                watch_type,
                json.dumps(watch_params),
                status,
                datetime.utcnow().isoformat() + "Z"
            ))
            conn.commit()
        return assumption_id

    def get_assumptions_for_decision(self, decision_id: str) -> List[Dict[str, Any]]:
        """Retrieves all tracked assumptions for a decision."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT * FROM decision_assumptions WHERE decision_id = ?
            """, (decision_id,))
            rows = cursor.fetchall()
            results = []
            for r in rows:
                item = dict(r)
                item["watch_params"] = json.loads(item.get("watch_params_json") or "{}")
                results.append(item)
            return results

    def extract_dependency_changes(self, text_or_diff: str) -> Dict[str, str]:
        """
        Extracts package name and new version from commit messages, PR text, or requirement diffs.
        Handles patterns like:
          - pydantic>=2.0.0
          - bump pydantic to 2.1.0
          - redis==5.0.1
          - upgrade stripe to 5.0.0
        """
        changes: Dict[str, str] = {}
        # Pattern 1: bump/upgrade <pkg> to <ver>
        for m in re.finditer(r"(?i)\b(?:bump|upgrade|update)\s+([a-zA-Z0-9_\-]+)\s+(?:to|from\s+[0-9.]+\s+to)\s+([0-9.]+)", text_or_diff):
            pkg, ver = m.groups()
            changes[pkg.lower().replace("-", "_")] = ver

        # Pattern 2: requirements.txt syntax in diff (+pkg==ver or +pkg>=ver)
        for m in re.finditer(r"^\+\s*([a-zA-Z0-9_\-]+)\s*(?:==|>=|~=)\s*([0-9.]+)", text_or_diff, re.MULTILINE):
            pkg, ver = m.groups()
            changes[pkg.lower().replace("-", "_")] = ver

        # Pattern 3: direct mention like 'pydantic 2.0' or 'pydantic==2.0'
        for m in re.finditer(r"\b([a-zA-Z0-9_\-]+)\s*(?:==|>=)\s*([0-9.]+)", text_or_diff):
            pkg, ver = m.groups()
            changes[pkg.lower().replace("-", "_")] = ver

        return changes

    def evaluate_event_for_staleness(self, event: Event, diff_text: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Evaluates whether an incoming event (commit, PR, issue) invalidates any decision assumptions.
        Returns a list of triggered staleness findings.
        """
        combined_text = f"{event.title or ''}\n{event.body or ''}\n{diff_text or ''}"
        dep_changes = self.extract_dependency_changes(combined_text)
        touched_files = set(event.artifacts_touched or [])
        triggered_findings = []

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            # Find all active/valid assumptions for decisions in the same repository
            cursor.execute("""
            SELECT da.*, d.title as decision_title, d.freshness as current_freshness, d.repo
            FROM decision_assumptions da
            JOIN decisions d ON da.decision_id = d.decision_id
            WHERE d.repo = ? AND da.status = 'valid'
            """, (event.repo,))
            assumptions = [dict(r) for r in cursor.fetchall()]

            now_iso = datetime.utcnow().isoformat() + "Z"

            for assump in assumptions:
                watch_type = assump["watch_type"]
                params = json.loads(assump.get("watch_params_json") or "{}")
                broken = False
                trigger_reason = ""

                # 1. Dependency Version Upgrade
                if watch_type == "dependency_version":
                    target_pkg = params.get("package", "").lower().replace("-", "_")
                    max_ver = params.get("max_version")
                    constraint = params.get("constraint") or params.get("target_version") or ""
                    
                    if target_pkg in dep_changes:
                        new_ver = dep_changes[target_pkg]
                        if check_version_violation(new_ver, constraint, max_version=max_ver):
                            broken = True
                            trigger_reason = (
                                f"Dependency '{target_pkg}' upgraded to {new_ver} (exceeds assumption '{assump['text']}'). "
                                f"Triggered by {event.source_type} #{event.source_id}."
                            )

                # 2. Config Value Change
                elif watch_type == "config_value":
                    cfg_key = params.get("config_key", "")
                    expected = params.get("expected_value")
                    # Check if diff alters the config key
                    if cfg_key and cfg_key in combined_text:
                        # Extract assignment like KEY = VAL
                        m = re.search(rf"\b{re.escape(cfg_key)}\s*[:=]\s*([^\s,;]+)", combined_text)
                        if m:
                            new_val = m.group(1).strip("'\"")
                            if str(new_val) != str(expected):
                                broken = True
                                trigger_reason = (
                                    f"Configuration '{cfg_key}' changed to '{new_val}' (expected '{expected}'). "
                                    f"Triggered by {event.source_type} #{event.source_id}."
                                )

                # 3. File Exists / Deleted File
                elif watch_type == "file_exists":
                    watched_file = params.get("file_path", "")
                    if watched_file and (watched_file in touched_files or watched_file in combined_text):
                        if (
                            "deleted file mode" in combined_text
                            or f"--- a/{watched_file}\n+++ /dev/null" in combined_text
                            or "delete" in (event.title or "").lower()
                        ):
                            broken = True
                            trigger_reason = (
                                f"Watched file '{watched_file}' was deleted or moved. "
                                f"Triggered by {event.source_type} #{event.source_id}."
                            )

                # 4. Manual Flag
                elif watch_type == "manual":
                    # Manual watches are only broken via explicit admin actions
                    pass

                if broken:
                    # Mark assumption broken
                    cursor.execute("""
                    UPDATE decision_assumptions
                    SET status = 'broken',
                        trigger_event_id = ?,
                        trigger_notes = ?,
                        last_checked_at = ?
                    WHERE assumption_id = ?
                    """, (event.event_id, trigger_reason, now_iso, assump["assumption_id"]))

                    # Transition decision freshness to 'stale'
                    cursor.execute("""
                    UPDATE decisions
                    SET freshness = 'stale'
                    WHERE decision_id = ?
                    """, (assump["decision_id"],))

                    finding = {
                        "decision_id": assump["decision_id"],
                        "decision_title": assump["decision_title"],
                        "assumption_id": assump["assumption_id"],
                        "assumption_text": assump["text"],
                        "watch_type": watch_type,
                        "trigger_event_id": event.event_id,
                        "trigger_url": event.source_url,
                        "trigger_reason": trigger_reason
                    }
                    triggered_findings.append(finding)

            conn.commit()

        return triggered_findings

    def revalidate_decision(
        self,
        decision_id: str,
        actor: str,
        reason: str,
        at: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Revalidates a stale decision:
        1. Transitions decisions.freshness to 'revalidated'.
        2. Sets all associated broken assumptions back to 'valid' with updated timestamp.
        3. Records audit log row in state_history documenting the revalidation.
        """
        now_iso = at or (datetime.utcnow().isoformat() + "Z")
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM decisions WHERE decision_id = ?", (decision_id,))
            dec = cursor.fetchone()
            if not dec:
                raise ValueError(f"Decision '{decision_id}' not found.")

            # Update decision freshness
            cursor.execute("""
            UPDATE decisions SET freshness = 'revalidated' WHERE decision_id = ?
            """, (decision_id,))

            # Reset assumptions to valid
            cursor.execute("""
            UPDATE decision_assumptions
            SET status = 'valid',
                last_checked_at = ?,
                trigger_notes = 'Revalidated by reviewer'
            WHERE decision_id = ?
            """, (now_iso, decision_id))

            # Record revalidation in state_history
            cursor.execute("PRAGMA table_info(state_history)")
            cols = {r["name"] for r in cursor.fetchall()}
            hist_id = f"hist_reval_{decision_id}_{int(datetime.utcnow().timestamp())}"
            notes_str = f"Revalidated decision freshness: {reason}"
            if "reconstructed" in cols:
                cursor.execute("""
                INSERT INTO state_history (history_id, decision_id, state, changed_at, changed_by, notes, reconstructed)
                VALUES (?, ?, ?, ?, ?, ?, 0)
                """, (hist_id, decision_id, dec["state"], now_iso, actor, notes_str))
            else:
                cursor.execute("""
                INSERT INTO state_history (history_id, decision_id, state, changed_at, changed_by, notes)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (hist_id, decision_id, dec["state"], now_iso, actor, notes_str))

            conn.commit()

        return {
            "decision_id": decision_id,
            "freshness": "revalidated",
            "actor": actor,
            "revalidated_at": now_iso,
            "notes": notes_str
        }

    def get_stale_review_items(self) -> List[Dict[str, Any]]:
        """
        Returns review-queue entries for all stale decisions, including:
        - Triggering change description
        - Clickable source link
        - 'Stale for N days' counter computed from trigger timestamp
        """
        items = []
        now = datetime.utcnow()
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT d.decision_id, d.title, d.freshness, d.repo, d.made_at,
                   da.assumption_id, da.text as assumption_text, da.watch_type,
                   da.trigger_event_id, da.trigger_notes, da.last_checked_at,
                   e.source_url, e.ts as event_ts, e.source_type, e.source_id
            FROM decisions d
            JOIN decision_assumptions da ON d.decision_id = da.decision_id
            LEFT JOIN events e ON da.trigger_event_id = e.event_id
            WHERE d.freshness IN ('stale', 'under_review') AND da.status = 'broken'
            ORDER BY da.last_checked_at DESC
            """)
            rows = cursor.fetchall()
            for r in rows:
                row = dict(r)
                # Compute stale days counter
                ref_ts_str = row.get("event_ts") or row.get("last_checked_at")
                stale_days = 0
                if ref_ts_str:
                    try:
                        clean_ts = ref_ts_str.replace("Z", "+00:00")
                        dt = datetime.fromisoformat(clean_ts).replace(tzinfo=None)
                        stale_days = max(0, (now - dt).days)
                    except Exception:
                        stale_days = 0

                trigger_url = row.get("source_url") or "#"
                queue_reason = (
                    row.get("trigger_notes")
                    or f"Assumption '{row['assumption_text']}' was broken (stale for {stale_days} days)"
                )

                items.append({
                    "item_type": "stale_decision",
                    "decision_id": row["decision_id"],
                    "title": f"Stale Decision: '{row['title']}'",
                    "freshness": row["freshness"],
                    "repo": row["repo"],
                    "assumption_id": row["assumption_id"],
                    "assumption_text": row["assumption_text"],
                    "watch_type": row["watch_type"],
                    "queue_reason": queue_reason,
                    "trigger_event_id": row.get("trigger_event_id"),
                    "trigger_url": trigger_url,
                    "stale_days": stale_days,
                    "made_at": row.get("event_ts") or row.get("made_at"),
                    "review_status": "pending_review"
                })

        return items
