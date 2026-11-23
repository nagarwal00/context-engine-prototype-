"""
Migration 009: keep state_history.repo_full_name populated.

Migration 007 backfilled repo_full_name once; rows written afterwards by lifecycle transitions,
review actions and revalidation were left NULL (Windows test failure 2026-11-23:
"Table state_history has 2 rows with unresolved repo_full_name").

This migration (see backend/integrity.py):
  1. creates trigger trg_state_history_repo_attribution, which copies the repository from the
     row's own decision whenever a row is inserted without one;
  2. backfills existing NULL/empty rows from their own decision.
Rows whose decision is missing or has no repository stay NULL (never fabricated). No row is
deleted and no column or table is added.
"""
import sqlite3

VERSION = 9
NAME = "state_history_attribution"


def upgrade(conn: sqlite3.Connection) -> None:
    from backend.integrity import backfill_state_history_attribution
    backfill_state_history_attribution(conn)


def downgrade(conn: sqlite3.Connection) -> None:
    conn.execute("DROP TRIGGER IF EXISTS trg_state_history_repo_attribution")
    # Backfilled values are correct data (copied from each row's decision) and are kept.
