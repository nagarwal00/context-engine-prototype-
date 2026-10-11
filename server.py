"""
Context Intelligence Framework - Web Server
Runs the prototype backend and serves the interactive frontend.

Environment variables (all optional):
  PORT            - TCP port to listen on (default: 8080)
  CIF_BIND        - Set to "0.0.0.0" to bind on all interfaces (default: 127.0.0.1)
  CIF_DB_PATH     - Path to the SQLite database file (default: context_intelligence.db next to this file)
  CIF_WEBHOOK_SECRET - HMAC secret for GitHub webhook verification
  GITHUB_TOKEN    - Personal access token for GitHub API calls
"""
import http.server
import json
import os
import sys
import urllib.parse
from backend.db import Database
from backend.api import APIHandler
from backend.seed_data import populate_seed_data
from backend.security import get_cors_origin, MAX_BODY_SIZE

# Configurable via environment (Phase 8.2)
PORT = int(os.environ.get("PORT", "8080"))
BIND_HOST = os.environ.get("CIF_BIND", "127.0.0.1")
_default_db = os.path.join(os.path.dirname(__file__), "context_intelligence.db")
DB_PATH = os.environ.get("CIF_DB_PATH", _default_db)
WEB_DIR = os.path.join(os.path.dirname(__file__), "web")


def check_bind_safety(host: str) -> None:
    """Refuses to bind on non-loopback addresses unless CIF_ADMIN_TOKEN is configured."""
    admin_token = os.environ.get("CIF_ADMIN_TOKEN", "").strip()
    if host not in ("127.0.0.1", "localhost", "::1") and not admin_token:
        raise SystemExit(
            f"Security Error: Refusing to bind on '{host}' without CIF_ADMIN_TOKEN configured. "
            "Set CIF_ADMIN_TOKEN or bind to 127.0.0.1."
        )


class ContextIntelligenceServer(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path.startswith("/api/"):
            headers_dict = {k: v for k, v in self.headers.items()}
            client_ip = self.client_address[0] if self.client_address else "127.0.0.1"

            ok, status_code, message = self.server.api_handler.check_authorization(
                "GET", parsed.path, headers_dict, client_ip
            )
            if not ok:
                self._send_json({"status": "error", "message": message}, status=status_code)
                return

            params = urllib.parse.parse_qs(parsed.query)
            res = self.server.api_handler.handle_get(parsed.path, params)
            self._send_json(res)
        else:
            # Fallback to serving web/ files
            super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path.startswith("/api/"):
            headers_dict = {k: v for k, v in self.headers.items()}
            client_ip = self.client_address[0] if self.client_address else "127.0.0.1"

            # Check authorization before reading/parsing request body
            ok, status_code, message = self.server.api_handler.check_authorization(
                "POST", parsed.path, headers_dict, client_ip
            )
            if not ok:
                self._send_json({"status": "error", "message": message}, status=status_code)
                return

            try:
                content_len = int(self.headers.get("Content-Length", 0))
            except (ValueError, TypeError):
                content_len = 0

            # Body size limit: 1 MB
            if content_len > MAX_BODY_SIZE:
                self._send_json(
                    {"status": "error", "message": "Payload too large: maximum body size is 1MB"},
                    status=413
                )
                return

            raw_body = self.rfile.read(content_len) if content_len > 0 else b"{}"

            # Route webhook separately (needs raw bytes for HMAC)
            if parsed.path == "/api/webhook/github":
                try:
                    body_json = json.loads(raw_body.decode("utf-8")) if raw_body else {}
                except Exception:
                    self._send_json({"status": "error", "message": "Invalid JSON in request body"}, status=400)
                    return
                result, webhook_status = self.server.api_handler.handle_webhook(
                    parsed.path, headers_dict, raw_body, body_json
                )
                self._send_json(result, status=webhook_status)
                return

            # For regular POST routes, parse JSON body
            try:
                body_json = json.loads(raw_body.decode("utf-8")) if raw_body else {}
                if not isinstance(body_json, dict):
                    self._send_json({"status": "error", "message": "Invalid JSON: body must be an object"}, status=400)
                    return
            except Exception:
                self._send_json({"status": "error", "message": "Invalid JSON in request body"}, status=400)
                return

            res = self.server.api_handler.handle_post(parsed.path, body_json)
            status = res.get("status_code", 200 if res.get("status") == "success" else 400)
            self._send_json(res, status=status)
        else:
            self.send_error(404, "Endpoint not found")

    def _send_json(self, data, status=200):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))

        # CORS: Default same-origin only; echo origin only if in CIF_CORS_ORIGINS allowlist
        origin = self.headers.get("Origin") if hasattr(self, "headers") and self.headers else None
        allowed_origin = get_cors_origin(origin)
        if allowed_origin:
            self.send_header("Access-Control-Allow-Origin", allowed_origin)
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Hub-Signature-256, X-GitHub-Event")

        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        origin = self.headers.get("Origin") if hasattr(self, "headers") and self.headers else None
        allowed_origin = get_cors_origin(origin)
        if allowed_origin:
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", allowed_origin)
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Hub-Signature-256, X-GitHub-Event")
            self.end_headers()
        else:
            self.send_response(204)
            self.end_headers()

    def log_message(self, format, *args):
        # Quiet standard output
        pass


# Ensure stdout is utf-8 compatible on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def run():
    print("=" * 70)
    print("  Context Intelligence Framework -- Living Decision History Prototype")
    print("=" * 70)

    check_bind_safety(BIND_HOST)

    db = Database(DB_PATH)
    # Check if database has decisions; if not, seed it
    with db.get_connection() as conn:
        cnt = conn.execute("SELECT COUNT(*) as c FROM decisions").fetchone()["c"]
        if cnt == 0:
            print("[*] Initializing pilot repositories and seed data...")
            populate_seed_data(db)
            print("[OK] Seed data loaded successfully!")
        else:
            print(f"[OK] Existing database loaded with {cnt} decisions.")

    api_handler = APIHandler(db)

    server_address = (BIND_HOST, PORT)
    httpd = http.server.ThreadingHTTPServer(server_address, ContextIntelligenceServer)
    httpd.api_handler = api_handler

    print(f"\n[SERVER LIVE] Prototype is live and running at: http://{BIND_HOST}:{PORT}/")
    print(f"[*] Serving all 9 UI surfaces, interactive Context Graph, and Review Queue.")
    print(f"[*] Press Ctrl+C to terminate.\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Shutting down server.")
        httpd.server_close()


if __name__ == "__main__":
    run()
