# Installation and Setup (verified on a fresh clone, 2026-11-21)

## Requirements
- Python 3.11+ (verified on 3.13; CI uses 3.11). No `pip install` needed.
- Optional: `git` (local-folder ingestion of real history), Node.js (`tools/check_js.py`),
  `cryptography` (encrypted GitHub token storage).

## 1. Clean installation
```bash
git clone https://github.com/nagarwal00/context-engine-prototype-.git
```
```bash
cd context-engine-prototype-
```
```bash
python tools/init_db.py --seed
```
This creates `context_intelligence.db`, applies migrations 001–008 and loads the two synthetic
demo repositories (`acme-eng/…`). It never deletes an existing database unless you pass `--fresh`.

## 2. Configuration (optional)
```bash
cp .env.example .env
```
Edit `.env`. Important keys:

| Key | Default | Meaning |
|---|---|---|
| `PORT` | 8080 | Any port works now (the UI no longer depends on 8080) |
| `CIF_BIND` | 127.0.0.1 | Public bind is refused while `CIF_DEV_MODE=1` |
| `CIF_DEV_MODE` | 1 in the example | Local admin rights for loopback callers (ingest, reseed). Use only on your own machine. |
| `CIF_ADMIN_TOKEN` | empty | Bearer token for admin endpoints when dev mode is off |
| `CIF_BASE_URL` | http://127.0.0.1:8080 | Public address of the server: used for the GitHub OAuth callback and the cookie `Secure` flag. (CSRF checks also accept the address you actually browse to.) |
| `CIF_DEMO_LOGIN` | 1 | "Sign in as Demo Developer" button |
| `GITHUB_APP_CLIENT_ID/SECRET` | empty | GitHub OAuth (optional) |
| `GITHUB_TOKEN` | empty | Raises GitHub API limits for ingestion |

## 3. Start
```bash
python server.py
```
Open the address printed (default http://127.0.0.1:8080/), choose **Register**, create a user with
a password of at least 8 characters, or click **Sign in as Demo Developer**.

## 4. Verify
```bash
python -m unittest discover -s tests
```
```bash
python run_demo.py
```
Expected: 409 tests OK (2 skipped); 21/21 demo checks.

## 5. Production notes
- Put the server behind HTTPS (reverse proxy), set `CIF_BASE_URL=https://…`, `CIF_DEV_MODE=0`,
  a strong `CIF_ADMIN_TOKEN`, `CIF_SESSION_SECRET`, and `CIF_BIND=0.0.0.0` only behind the proxy.
- Docker: `docker build -t cif .` then
  `docker run -p 8080:8080 -v cif-data:/app/data --env-file .env cif` (`.env` is not copied into the image).
- **GitHub Pages hosts only the static snapshot** (`docs/`). It cannot run Python: no sign-in,
  no ingestion, no persistence. The badge shows "Static snapshot".

## 6. Database backup and recovery
```bash
python -c "import sqlite3; s=sqlite3.connect('context_intelligence.db'); d=sqlite3.connect('backup.db'); s.backup(d)"
```
Restore by stopping the server and copying `backup.db` over `context_intelligence.db`.
Check integrity at any time:
```bash
python -c "import sqlite3; c=sqlite3.connect('context_intelligence.db'); print(c.execute('PRAGMA integrity_check').fetchone(), c.execute('SELECT COUNT(*) FROM v_ungrounded_decisions').fetchone())"
```
