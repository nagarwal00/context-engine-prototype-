# Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `Security Error: refusing to bind on '0.0.0.0' while CIF_DEV_MODE=1` | Dev mode gives local callers admin rights; it must not be exposed | Use `CIF_BIND=127.0.0.1`, or set `CIF_DEV_MODE=0` and `CIF_ADMIN_TOKEN` |
| `OSError: [Errno 98] Address already in use` | Another server on the port | Stop it, or `PORT=8090 python server.py` (any port works) |
| Login says "Invalid username or password" for an old account | Accounts created before the audit had **no password** (the old login ignored passwords) | Register a new account, or use *Sign in as Demo Developer* |
| `403 CSRF_ORIGIN_MISMATCH` | Request came from another site, or a proxy rewrites Host | Use the dashboard from the server's own address; behind a proxy set `CIF_BASE_URL` to the public URL |
| `403 HOST_NOT_ALLOWED` | Dev mode only accepts `localhost` / `127.0.0.1` in the address bar | Browse to http://127.0.0.1:PORT |
| `415 UNSUPPORTED_MEDIA_TYPE` | API POST without `Content-Type: application/json` | Send JSON with that header |
| `429 RATE_LIMIT_EXCEEDED` | Too many requests (auth 10/min, ingest 5/min, expensive 15/min, other 300/min) | Wait for `Retry-After` seconds; tune `CIF_RATE_LIMIT_*` |
| Badge shows **Backend unreachable** | The page cannot reach `server.py` | Restart the server, reload the page |
| Badge shows **Static snapshot** on your own server | You opened `docs/` or a `file://` page | Open the URL printed by `server.py` (it serves `web/`) |
| Ingest: `GitHub refused the request … (HTTP 403)` | Unauthenticated GitHub limit (60/h) | Set `GITHUB_TOKEN` or paste a token in the dialog |
| Ingest: `Network ingestion disabled in local-only mode` | `CIF_LOCAL_ONLY=1` | Unset it or ingest a local folder |
| Local folder ingest shows author `unknown` | Folder has no `.git` history | Ingest a git clone, or run `demo_sample_repo/setup_git_history.py` inside a copy of the demo folder |
| `demo_sample_repo/` is empty after cloning | It is committed as a broken submodule pointer | Use the copy from the original ZIP (see FINAL_PROJECT_STATUS, decision needed) |
| `IntegrityError: CIF invariant violated …` | Attempt to delete the only evidence of, or promote without evidence, a grounded decision | Intended protection; reopen/supersede the decision first |
| `validate_whybench.py` hash error | Dataset file content changed | Restore `backend/evaluation/whybench/questions.json` from Git |
| Server returns `500 INTERNAL_ERROR` | Unexpected bug | Find the `request_id` in `logs/error.log` |
