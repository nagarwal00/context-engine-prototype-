"""
Offline Slack Workspace Export Adapter (Step 5.5)
Parses Slack workspace export directories containing:
- users.json (user id, name, real_name, profile.email)
- channels.json (channel id, name)
- per-channel date files (YYYY-MM-DD.json with user, ts, text, thread_ts)

Maps messages to Event(source_type="slack_message"), resolves users through
users.json and IdentityResolver, groups messages by thread (independence_key = thread),
and runs Sanitizer BEFORE SQLite persistence.
"""
import os
import json
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Set
from backend.models import Event
from backend.db import Database
from backend.ingestion.identity import IdentityResolver
from backend.ingestion.sanitizer import sanitize_event


class SlackExportAdapter:
    def __init__(self, db: Database, identity_resolver: Optional[IdentityResolver] = None):
        self.db = db
        self.identity_resolver = identity_resolver or IdentityResolver(db)

    def _slack_ts_to_iso(self, ts_str: str) -> str:
        """Converts Slack Unix epoch timestamp string (e.g. '1673776800.000100') to ISO8601 UTC."""
        try:
            epoch = float(ts_str.split(".")[0])
            dt = datetime.fromtimestamp(epoch, tz=timezone.utc)
            return dt.isoformat()
        except Exception:
            return datetime.now(timezone.utc).isoformat()

    def ingest_export(self, export_dir: str, repo: str) -> Dict[str, Any]:
        """
        Ingests a Slack workspace export folder.
        Returns a dictionary summary of ingested events and threads.
        """
        if not os.path.exists(export_dir):
            raise FileNotFoundError(f"Slack export directory not found: {export_dir}")

        # 1. Parse users.json
        users_file = os.path.join(export_dir, "users.json")
        user_map: Dict[str, Dict[str, str]] = {}
        if os.path.exists(users_file):
            with open(users_file, "r", encoding="utf-8") as f:
                user_list = json.load(f)
                for u in user_list:
                    u_id = u.get("id")
                    if not u_id:
                        continue
                    profile = u.get("profile") or {}
                    email = profile.get("email") or ""
                    real_name = u.get("real_name") or profile.get("real_name") or u.get("name") or ""
                    name = u.get("name") or ""

                    # Resolve canonical author identity
                    canonical_author = (
                        self.identity_resolver.resolve(email)
                        if email
                        else self.identity_resolver.resolve(real_name or name)
                    )

                    user_map[u_id] = {
                        "name": name,
                        "real_name": real_name,
                        "email": email,
                        "canonical_id": canonical_author
                    }

        # 2. Parse channels.json
        channels_file = os.path.join(export_dir, "channels.json")
        channel_map: Dict[str, str] = {} # name -> id
        if os.path.exists(channels_file):
            with open(channels_file, "r", encoding="utf-8") as f:
                channel_list = json.load(f)
                for c in channel_list:
                    c_id = c.get("id", "")
                    c_name = c.get("name", "")
                    if c_name:
                        channel_map[c_name] = c_id

        # 3. Traverse channel folders
        ingested_events: List[Event] = []
        threads_seen: Set[str] = set()
        channels_processed: Set[str] = set()

        for entry in os.listdir(export_dir):
            channel_dir = os.path.join(export_dir, entry)
            if not os.path.isdir(channel_dir):
                continue

            channel_name = entry
            channels_processed.add(channel_name)
            channel_id = channel_map.get(channel_name, f"C_{channel_name}")

            for fname in os.listdir(channel_dir):
                if not fname.endswith(".json"):
                    continue

                fpath = os.path.join(channel_dir, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        messages = json.load(f)
                except Exception:
                    continue

                if not isinstance(messages, list):
                    continue

                for msg in messages:
                    if not isinstance(msg, dict):
                        continue

                    # Filter out system joins/leaves
                    sub_type = msg.get("subtype")
                    if sub_type in ("channel_join", "channel_leave", "bot_message"):
                        continue

                    ts = msg.get("ts")
                    if not ts:
                        continue

                    user_id = msg.get("user") or "unknown"
                    user_info = user_map.get(user_id, {})
                    author = user_info.get("canonical_id") or user_id

                    thread_ts = msg.get("thread_ts") or ts
                    is_thread_root = (thread_ts == ts)

                    independence_key = f"slack_thread:{channel_name}:{thread_ts}"
                    threads_seen.add(independence_key)

                    # Build Slack source URL
                    clean_ts = ts.replace(".", "")
                    source_url = f"https://slack.com/archives/{channel_id}/p{clean_ts}"

                    iso_ts = self._slack_ts_to_iso(ts)
                    text = msg.get("text") or ""

                    # Formulate event ID
                    event_id = f"evt_slack_{channel_name}_{clean_ts}"

                    # Parent event link if this is a reply in a thread
                    parent_ids = []
                    if not is_thread_root:
                        root_clean_ts = thread_ts.replace(".", "")
                        parent_ids.append(f"evt_slack_{channel_name}_{root_clean_ts}")

                    raw_meta = {
                        "slack_channel": channel_name,
                        "slack_channel_id": channel_id,
                        "slack_ts": ts,
                        "thread_ts": thread_ts,
                        "independence_key": independence_key,
                        "slack_user_id": user_id,
                        "user_real_name": user_info.get("real_name", "")
                    }

                    ev = Event(
                        event_id=event_id,
                        source_type="slack_message",
                        source_id=f"{channel_name}:{ts}",
                        source_url=source_url,
                        repo=repo,
                        author=author,
                        timestamp=iso_ts,
                        title=f"Slack #{channel_name} discussion: {text[:50]}...",
                        body=text,
                        artifacts_touched=[],
                        parent_event_ids=parent_ids,
                        raw_metadata=raw_meta
                    )

                    # CRITICAL: Sanitize event BEFORE persistence (Step 5.1 / §5.5)
                    sanitized_ev = sanitize_event(ev)

                    # Upsert to database
                    self.db.upsert_event(sanitized_ev)
                    ingested_events.append(sanitized_ev)

        return {
            "status": "success",
            "repo": repo,
            "messages_ingested": len(ingested_events),
            "threads_count": len(threads_seen),
            "channels_count": len(channels_processed),
            "channels": sorted(list(channels_processed)),
            "events": [e.to_dict() for e in ingested_events]
        }
