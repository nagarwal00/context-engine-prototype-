"""
Migration 007: Auth, Sessions, Repositories, Ingestion Jobs, and Repo Attribution
Implements Step 7.2 of docs/process/ANTIGRAVITY_HANDOFF_V3_EXTENSION.md:
- Creates users table
- Creates sessions table (storing SHA-256 hash of session token)
- Creates oauth_states table
- Creates ext_codes table
- Creates repos table (visibility in 'demo', 'public', 'private')
- Creates repo_access table
- Creates repo_reviewers table
- Creates ingest_jobs table
- Creates user_tokens table (for optional R1 encrypted refresh tokens)
- Additively adds repo_full_name column to all data tables, creates indexes, and backfills attribution.
- Seeds existing demo repositories as visibility='demo'.
"""
import sqlite3
import datetime

VERSION = 7
NAME = "auth_and_repo_tables"


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name = ?", (table_name,))
    return cur.fetchone() is not None


def _column_exists(conn: sqlite3.Connection, table_name: str, col_name: str) -> bool:
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table_name});")
    cols = [row[1] for row in cur.fetchall()]
    return col_name in cols


def _add_column_if_missing(conn: sqlite3.Connection, table_name: str, col_def: str, col_name: str) -> None:
    if _table_exists(conn, table_name) and not _column_exists(conn, table_name, col_name):
        conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {col_def};")


def upgrade(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()

    # 1. Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        github_id INTEGER UNIQUE NOT NULL,
        login TEXT NOT NULL,
        avatar_url TEXT,
        created_at TEXT NOT NULL,
        last_login_at TEXT NOT NULL
    );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_login ON users(login);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_github_id ON users(github_id);")

    # 2. Sessions Table (stores SHA-256 hash of session token)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        session_hash TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        client TEXT NOT NULL,
        created_at TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        last_seen_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at);")

    # 3. OAuth States Table (single use, 10-minute lifetime)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS oauth_states (
        state_hash TEXT PRIMARY KEY,
        created_at TEXT NOT NULL,
        next_path TEXT,
        client TEXT,
        ext_id TEXT
    );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_oauth_states_created ON oauth_states(created_at);")

    # 4. Extension One-Time Codes Table (single use, 60-second lifetime)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ext_codes (
        code_hash TEXT PRIMARY KEY,
        session_hash TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (session_hash) REFERENCES sessions(session_hash) ON DELETE CASCADE
    );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ext_codes_created ON ext_codes(created_at);")

    # 5. Repositories Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS repos (
        repo_full_name TEXT PRIMARY KEY,
        github_repo_id INTEGER,
        visibility TEXT NOT NULL CHECK (visibility IN ('demo', 'public', 'private')),
        added_by_user_id INTEGER,
        added_at TEXT,
        last_synced_at TEXT,
        partial INTEGER DEFAULT 0,
        stats_json TEXT,
        FOREIGN KEY (added_by_user_id) REFERENCES users(user_id) ON DELETE SET NULL
    );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_repos_visibility ON repos(visibility);")

    # 6. Repository Access Table (per-user cached permissions)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS repo_access (
        user_id INTEGER NOT NULL,
        repo_full_name TEXT NOT NULL,
        level TEXT NOT NULL,
        verified_at TEXT NOT NULL,
        PRIMARY KEY (user_id, repo_full_name),
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
        FOREIGN KEY (repo_full_name) REFERENCES repos(repo_full_name) ON DELETE CASCADE
    );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_repo_access_repo ON repo_access(repo_full_name);")

    # 7. Repository Reviewers Table (Step 7.4 fallback)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS repo_reviewers (
        repo_full_name TEXT NOT NULL,
        user_id INTEGER NOT NULL,
        added_by INTEGER,
        added_at TEXT,
        PRIMARY KEY (repo_full_name, user_id),
        FOREIGN KEY (repo_full_name) REFERENCES repos(repo_full_name) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    """)

    # 8. Ingestion Jobs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ingest_jobs (
        job_id TEXT PRIMARY KEY,
        repo_full_name TEXT NOT NULL,
        requested_by INTEGER,
        status TEXT NOT NULL CHECK (status IN ('queued', 'running', 'needs_relogin', 'failed', 'partial', 'done', 'cancelled')),
        phase TEXT,
        progress_json TEXT,
        error_code TEXT,
        cursor_json TEXT,
        created_at TEXT NOT NULL,
        started_at TEXT,
        finished_at TEXT,
        FOREIGN KEY (repo_full_name) REFERENCES repos(repo_full_name) ON DELETE CASCADE,
        FOREIGN KEY (requested_by) REFERENCES users(user_id) ON DELETE SET NULL
    );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ingest_jobs_repo ON ingest_jobs(repo_full_name);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ingest_jobs_status ON ingest_jobs(status);")

    # 9. User Encrypted Tokens Table (R1 storage)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_tokens (
        user_id INTEGER PRIMARY KEY,
        token_cipher BLOB,
        refresh_cipher BLOB,
        expires_at TEXT,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    """)

    # 10. Seed Demo Repositories
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    known_demo_repos = [
        "acme-eng/thermal-control-system",
        "acme-eng/distributed-cache-service"
    ]
    for r in known_demo_repos:
        cursor.execute("""
        INSERT OR IGNORE INTO repos (repo_full_name, visibility, added_at, partial)
        VALUES (?, 'demo', ?, 0);
        """, (r, now_iso))

    # Also register any repo already found in decisions or events as demo
    if _table_exists(conn, "decisions"):
        cursor.execute("""
        INSERT OR IGNORE INTO repos (repo_full_name, visibility, added_at, partial)
        SELECT DISTINCT repo, 'demo', ?, 0 FROM decisions WHERE repo IS NOT NULL AND repo != '';
        """, (now_iso,))

    if _table_exists(conn, "events"):
        cursor.execute("""
        INSERT OR IGNORE INTO repos (repo_full_name, visibility, added_at, partial)
        SELECT DISTINCT repo, 'demo', ?, 0 FROM events WHERE repo IS NOT NULL AND repo != '';
        """, (now_iso,))

    # 11. Additive repo_full_name column on all data tables
    tables_to_augment = [
        "events",
        "entities",
        "decisions",
        "edges",
        "decision_claims",
        "claim_evidence",
        "decision_evidence",
        "decision_artifacts",
        "state_history",
        "guard_rules",
        "decision_assumptions",
        "finding_feedback",
        "ambiguous_findings"
    ]

    for tbl in tables_to_augment:
        _add_column_if_missing(conn, tbl, "repo_full_name TEXT", "repo_full_name")
        if _table_exists(conn, tbl):
            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{tbl}_repo_full_name ON {tbl}(repo_full_name);")

    # 12. Backfill repo_full_name for each table

    # events, entities, decisions, ambiguous_findings have a 'repo' column
    for tbl in ["events", "entities", "decisions", "ambiguous_findings"]:
        if _table_exists(conn, tbl) and _column_exists(conn, tbl, "repo"):
            cursor.execute(f"""
            UPDATE {tbl}
            SET repo_full_name = repo
            WHERE repo_full_name IS NULL OR repo_full_name = '';
            """)

    # decision-linked tables
    for tbl in ["decision_claims", "decision_evidence", "decision_artifacts", "state_history", "guard_rules", "decision_assumptions"]:
        if _table_exists(conn, tbl) and _table_exists(conn, "decisions") and _column_exists(conn, tbl, "decision_id"):
            cursor.execute(f"""
            UPDATE {tbl}
            SET repo_full_name = (
                SELECT repo FROM decisions WHERE decisions.decision_id = {tbl}.decision_id
            )
            WHERE repo_full_name IS NULL OR repo_full_name = '';
            """)

    # claim_evidence links via event_id
    if _table_exists(conn, "claim_evidence") and _table_exists(conn, "events") and _column_exists(conn, "claim_evidence", "event_id"):
        cursor.execute("""
        UPDATE claim_evidence
        SET repo_full_name = (
            SELECT repo FROM events WHERE events.event_id = claim_evidence.event_id
        )
        WHERE repo_full_name IS NULL OR repo_full_name = '';
        """)

    # finding_feedback links via decision_id (where present)
    if _table_exists(conn, "finding_feedback") and _table_exists(conn, "decisions") and _column_exists(conn, "finding_feedback", "decision_id"):
        cursor.execute("""
        UPDATE finding_feedback
        SET repo_full_name = (
            SELECT repo FROM decisions WHERE decisions.decision_id = finding_feedback.decision_id
        )
        WHERE (repo_full_name IS NULL OR repo_full_name = '') AND decision_id IS NOT NULL;
        """)

    # edges links from_id / to_id
    if _table_exists(conn, "edges"):
        # 1. from_id as decision
        if _table_exists(conn, "decisions"):
            cursor.execute("""
            UPDATE edges
            SET repo_full_name = (
                SELECT repo FROM decisions WHERE decisions.decision_id = edges.from_id
            )
            WHERE (repo_full_name IS NULL OR repo_full_name = '') AND from_type = 'decision';
            """)
        # 2. from_id as entity
        if _table_exists(conn, "entities"):
            cursor.execute("""
            UPDATE edges
            SET repo_full_name = (
                SELECT repo FROM entities WHERE entities.entity_id = edges.from_id
            )
            WHERE (repo_full_name IS NULL OR repo_full_name = '') AND from_type = 'entity';
            """)
        # 3. to_id as decision
        if _table_exists(conn, "decisions"):
            cursor.execute("""
            UPDATE edges
            SET repo_full_name = (
                SELECT repo FROM decisions WHERE decisions.decision_id = edges.to_id
            )
            WHERE (repo_full_name IS NULL OR repo_full_name = '') AND to_type = 'decision';
            """)
        # 4. to_id as entity
        if _table_exists(conn, "entities"):
            cursor.execute("""
            UPDATE edges
            SET repo_full_name = (
                SELECT repo FROM entities WHERE entities.entity_id = edges.to_id
            )
            WHERE (repo_full_name IS NULL OR repo_full_name = '') AND to_type = 'entity';
            """)
        # 5. to_id as event
        if _table_exists(conn, "events"):
            cursor.execute("""
            UPDATE edges
            SET repo_full_name = (
                SELECT repo FROM events WHERE events.event_id = edges.to_id
            )
            WHERE (repo_full_name IS NULL OR repo_full_name = '') AND to_type = 'event';
            """)
