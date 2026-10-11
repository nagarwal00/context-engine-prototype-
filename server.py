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

# Configurable via environment (Phase 8.2)
PORT = int(os.environ.get("PORT", "8080"))
BIND_HOST = os.environ.get("CIF_BIND", "127.0.0.1")
_default_db = os.path.join(os.path.dirname(__file__), "context_intelligence.db")
DB_PATH = os.environ.get("CIF_DB_PATH", _default_db)
WEB_DIR = os.path.join(os.path.dirname(__file__), "web")


class ContextIntelligenceServer(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path.startswith("/api/"):
            params = urllib.parse.parse_qs(parsed.query)
            res = self.server.api_handler.handle_get(parsed.path, params)
            self._send_json(res)
        else:
            # Fallback to serving web/ files
            super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path.startswith("/api/"):
            content_len = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(content_len) if content_len > 0 else b"{}"
            try:
                body_json = json.loads(raw_body.decode("utf-8"))
            except Exception:
                body_json = {}

            # Route webhook separately (needs raw bytes for HMAC)
            if parsed.path == "/api/webhook/github":
                headers_dict = {k: v for k, v in self.headers.items()}
                result, status_code = self.server.api_handler.handle_webhook(
                    parsed.path, headers_dict, raw_body, body_json
                )
                self._send_json(result, status=status_code)
            else:
                res = self.server.api_handler.handle_post(parsed.path, body_json)
                self._send_json(res)
        else:
            self.send_error(404, "Endpoint not found")

    def _send_json(self, data, status=200):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Hub-Signature-256, X-GitHub-Event")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Hub-Signature-256, X-GitHub-Event")
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
