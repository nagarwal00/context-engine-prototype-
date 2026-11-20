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
import datetime
import hashlib
import http.server
import json
import os
import re
import sys
import time
import urllib.parse
import uuid
import zlib
from backend.db import Database
from backend.api import APIHandler
from backend.seed_data import populate_seed_data
from backend.security import get_cors_origin, MAX_BODY_SIZE
from backend.logging_config import setup_logging, get_logger, set_request_id
from backend.rate_limiter import get_rate_limiter

setup_logging()
server_logger = get_logger("cif.server")
api_logger = get_logger("cif.api")

def load_dotenv(dotenv_path: str = None) -> None:
    if dotenv_path is None:
        dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
    if not os.path.isfile(dotenv_path):
        return
    try:
        with open(dotenv_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip("'\"")
                if k and k not in os.environ:
                    os.environ[k] = v
    except Exception:
        pass

load_dotenv()

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

    def _init_request_context(self):
        self._start_time = time.time()
        self._request_id = self.headers.get("X-Request-ID") or str(uuid.uuid4())
        set_request_id(self._request_id)

    def _get_client_key(self) -> str:
        auth_hdr = self.headers.get("Authorization", "")
        if auth_hdr.lower().startswith("bearer "):
            token = auth_hdr.split(" ", 1)[1].strip()
            if token:
                return f"user:{hashlib.sha256(token.encode('utf-8')).hexdigest()[:16]}"
        cookie_hdr = self.headers.get("Cookie", "")
        if "cif_session=" in cookie_hdr:
            match = re.search(r"cif_session=([a-zA-Z0-9_\-\.]+)", cookie_hdr)
            if match:
                return f"user:{hashlib.sha256(match.group(1).encode('utf-8')).hexdigest()[:16]}"
        client_ip = self.client_address[0] if hasattr(self, "client_address") else "127.0.0.1"
        return f"ip:{client_ip}"

    def _check_rate_limit(self, path: str) -> bool:
        clean_path = path.split("?")[0].rstrip("/")
        if not clean_path:
            clean_path = "/"
        if clean_path in ("/healthz", "/api/healthz", "/api/diagnostics", "/api/system/status"):
            return True
        if not (clean_path.startswith("/api/") or clean_path.startswith("/auth/")):
            return True

        category = get_rate_limiter().get_category_for_path(clean_path, method=self.command)
        key = self._get_client_key()
        allowed, retry_after, remaining, limit = get_rate_limiter().check_rate_limit(key, category=category)
        if not allowed:
            self._send_json({
                "status": "error",
                "error_code": "RATE_LIMIT_EXCEEDED",
                "message": f"Rate limit exceeded for category '{category}'. Please wait {retry_after} seconds before retrying.",
                "retry_after": retry_after,
                "category": category,
                "limit": limit
            }, status=429, extra_headers={
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(retry_after)
            })
            return False
        return True

    def end_headers(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path.endswith(".html") or parsed.path.endswith(".css") or parsed.path.endswith(".js") or parsed.path in ("", "/"):
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
        super().end_headers()

    def _send_redirect(self, location: str, extra_headers: dict = None, status: int = 302):
        try:
            req_id = getattr(self, "_request_id", None) or str(uuid.uuid4())
            self.send_response(status)
            self.send_header("Location", location)
            self.send_header("X-Request-ID", req_id)
            if extra_headers:
                for k, v in extra_headers.items():
                    if k.lower() != "location":
                        self.send_header(k, v)
            self.end_headers()
            start_time = getattr(self, "_start_time", None)
            latency_ms = round((time.time() - start_time) * 1000, 2) if start_time else 0.0
            client_ip = self.client_address[0] if hasattr(self, "client_address") else "-"
            api_logger.info(f"{self.command} {self.path} -> {status} ({latency_ms}ms) [client={client_ip}]")
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_GET(self):
        self._init_request_context()
        parsed = urllib.parse.urlparse(self.path)
        if not self._check_rate_limit(parsed.path):
            return
        if parsed.path in ("/healthz", "/api/healthz"):
            res = self.server.api_handler.handle_get(parsed.path, {}, headers={})
            self._send_json(res, status=200)
            return

        if parsed.path in ("/dashboard", "/repos", "/dashboard.html"):
            from backend.auth.sessions import extract_session_token, get_session
            headers_dict = {k: v for k, v in self.headers.items()}
            token, _ = extract_session_token(headers_dict)
            session = get_session(self.server.api_handler.db, token) if token else None
            if not session:
                target_url = parsed.path
                if parsed.query:
                    target_url += "?" + parsed.query
                self._send_redirect("/login.html?next=" + urllib.parse.quote(target_url), status=302)
                return
            if parsed.path in ("/dashboard", "/repos"):
                target = "/dashboard.html"
                if parsed.query:
                    target += "?" + parsed.query
                self._send_redirect(target, status=302)
                return

        if parsed.path.startswith("/auth/"):
            params = urllib.parse.parse_qs(parsed.query)
            if parsed.path == "/auth/github/login":
                from backend.auth.github_login import initiate_github_login
                next_path = params.get("next", [None])[0]
                client = params.get("client", ["web"])[0]
                ext_id = params.get("ext_id", [None])[0]
                status, loc, extra_h = initiate_github_login(
                    self.server.api_handler.db, next_path=next_path, client=client, ext_id=ext_id
                )
                if status == 302:
                    self._send_redirect(loc, extra_headers=extra_h)
                else:
                    self._send_json({"status": "error", "message": loc}, status=status)
                return

            elif parsed.path == "/auth/github/callback":
                from backend.auth.github_login import handle_github_callback
                status, target, extra_h = handle_github_callback(
                    self.server.api_handler.db, params
                )
                if status == 302:
                    self._send_redirect(target, extra_headers=extra_h)
                else:
                    self._send_json({"status": "error", "message": target}, status=status)
                return

            elif parsed.path == "/auth/demo/login":
                next_path = params.get("next", ["/dashboard.html"])[0]
                now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
                with self.server.api_handler.db.get_connection() as conn:
                    user_row = conn.execute("SELECT user_id FROM users WHERE login = 'demo-developer'").fetchone()
                    if user_row:
                        user_id = user_row["user_id"]
                        conn.execute("UPDATE users SET last_login_at = ? WHERE user_id = ?", (now_str, user_id))
                    else:
                        cur = conn.execute("""
                        INSERT INTO users (github_id, login, avatar_url, created_at, last_login_at)
                        VALUES (?, ?, ?, ?, ?)
                        """, (999999, "demo-developer", "https://avatars.githubusercontent.com/u/583231?v=4", now_str, now_str))
                        user_id = cur.lastrowid
                from backend.auth.sessions import create_session, build_session_cookie
                from backend.config import get_config
                raw_token, _ = create_session(self.server.api_handler.db, user_id=user_id, client="web")
                cookie_hdr = build_session_cookie(raw_token, get_config().get_base_url())
                self._send_redirect(next_path or "/dashboard.html", extra_headers={"Set-Cookie": cookie_hdr})
                return

            elif parsed.path == "/auth/me":
                from backend.auth.sessions import extract_session_token, get_session
                headers_dict = {k: v for k, v in self.headers.items()}
                token, _ = extract_session_token(headers_dict)
                session = get_session(self.server.api_handler.db, token) if token else None
                if session:
                    self._send_json({
                        "status": "success",
                        "authenticated": True,
                        "user": {
                            "login": session["login"],
                            "avatar_url": session["avatar_url"],
                            "user_id": session["user_id"]
                        }
                    }, status=200)
                else:
                    self._send_json({
                        "status": "success",
                        "authenticated": False,
                        "user": None
                    }, status=200)
                return

            elif parsed.path in ("/auth/logout", "/logout"):
                from backend.auth.sessions import extract_session_token, delete_session, build_logout_cookie
                from backend.config import get_config
                headers_dict = {k: v for k, v in self.headers.items()}
                token, _ = extract_session_token(headers_dict)
                if token:
                    delete_session(self.server.api_handler.db, token)
                logout_cookie = build_logout_cookie(get_config().get_base_url())
                self._send_redirect("/index.html?logged_out=1", extra_headers={"Set-Cookie": logout_cookie})
                return

            else:
                self.send_error(404, "Endpoint not found")
                return

        elif parsed.path.startswith("/api/"):
            headers_dict = {k: v for k, v in self.headers.items()}
            client_ip = self.client_address[0] if self.client_address else "127.0.0.1"
            params = urllib.parse.parse_qs(parsed.query)

            ok, status_code, message = self.server.api_handler.check_authorization(
                "GET", parsed.path, headers_dict, client_ip, query_params=params
            )
            if not ok:
                self._send_json({"status": "error", "message": message}, status=status_code)
                return

            res = self.server.api_handler.handle_get(parsed.path, params, headers=headers_dict)
            status = res.get("status_code", 200)
            self._send_json(res, status=status)
        else:
            # Fallback to serving web/ files
            super().do_GET()

    def do_POST(self):
        self._init_request_context()
        parsed = urllib.parse.urlparse(self.path)
        if not self._check_rate_limit(parsed.path):
            return
        params = urllib.parse.parse_qs(parsed.query)
        headers_dict = {k: v for k, v in self.headers.items()}
        client_ip = self.client_address[0] if self.client_address else "127.0.0.1"

        # CSRF check: state-changing cookie requests must carry matching Origin
        from backend.auth.sessions import extract_session_token, validate_csrf_origin
        from backend.config import get_config
        _, auth_type = extract_session_token(headers_dict)
        if auth_type == "cookie":
            origin = self.headers.get("Origin")
            if not validate_csrf_origin(origin, get_config().get_base_url()):
                self._send_json({"status": "error", "message": "CSRF check failed: Origin header mismatch"}, status=403)
                return

        if parsed.path.startswith("/auth/"):
            try:
                content_len = int(self.headers.get("Content-Length", 0))
            except (ValueError, TypeError):
                content_len = 0
            if content_len > MAX_BODY_SIZE:
                self.close_connection = True
                try:
                    remaining = content_len
                    while remaining > 0:
                        chunk = self.rfile.read(min(remaining, 65536))
                        if not chunk:
                            break
                        remaining -= len(chunk)
                except Exception:
                    pass
                self._send_json(
                    {"status": "error", "error_code": "PAYLOAD_TOO_LARGE", "message": "Payload too large: maximum body size is 1MB"},
                    status=413,
                    extra_headers={"Connection": "close"}
                )
                return

            raw_body = self.rfile.read(content_len) if content_len > 0 else b"{}"
            try:
                body_json = json.loads(raw_body.decode("utf-8")) if raw_body else {}
            except Exception:
                body_json = {}

            if parsed.path in ("/auth/extension/exchange", "/auth/token/exchange", "/api/auth/token/exchange"):
                from backend.auth.sessions import exchange_extension_code
                code = body_json.get("code")
                res = exchange_extension_code(self.server.api_handler.db, code)
                if res:
                    self._send_json(res, status=200)
                else:
                    self._send_json({"status": "error", "message": "Invalid or expired authorization code"}, status=400)
                return

            elif parsed.path in ("/auth/logout", "/logout", "/api/auth/logout"):
                from backend.auth.sessions import delete_session, build_logout_cookie
                from backend.config import get_config
                token, _ = extract_session_token(headers_dict)
                if token:
                    delete_session(self.server.api_handler.db, token)
                logout_cookie = build_logout_cookie(get_config().get_base_url())
                self._send_json({"status": "success", "message": "Logged out"}, status=200, extra_headers={"Set-Cookie": logout_cookie})
                return

            elif parsed.path in ("/auth/login", "/auth/register", "/api/auth/login", "/api/auth/register"):
                username = (body_json.get("username") or body_json.get("login") or "").strip()
                if not username:
                    self._send_json({"status": "error", "message": "Username is required"}, status=400)
                    return
                if not re.match(r"^[a-zA-Z0-9_\-\.@+]+$", username):
                    self._send_json({"status": "error", "message": "Invalid characters in username"}, status=400)
                    return

                is_register = parsed.path.endswith("/register") or body_json.get("action") == "register"
                now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
                with self.server.api_handler.db.get_connection() as conn:
                    user_row = conn.execute("SELECT user_id, login FROM users WHERE login = ?", (username,)).fetchone()
                    if user_row:
                        user_id = user_row["user_id"]
                        conn.execute("UPDATE users SET last_login_at = ? WHERE user_id = ?", (now_str, user_id))
                    else:
                        synthetic_github_id = 100000 + (zlib.crc32(username.encode("utf-8")) % 8900000)
                        avatar = f"https://avatars.githubusercontent.com/u/{synthetic_github_id}?v=4"
                        cur = conn.execute("""
                        INSERT INTO users (github_id, login, avatar_url, created_at, last_login_at)
                        VALUES (?, ?, ?, ?, ?)
                        """, (synthetic_github_id, username, avatar, now_str, now_str))
                        user_id = cur.lastrowid

                from backend.auth.sessions import create_session, build_session_cookie
                from backend.config import get_config
                raw_token, _ = create_session(self.server.api_handler.db, user_id=user_id, client="web")
                cookie_hdr = build_session_cookie(raw_token, get_config().get_base_url())
                next_target = body_json.get("next") or params.get("next", ["/dashboard.html"])[0] or "/dashboard.html"
                if not next_target.startswith("/") or next_target.startswith("//"):
                    next_target = "/dashboard.html"
                self._send_json({
                    "status": "success",
                    "message": f"Successfully {'registered' if is_register else 'signed in'} as {username}",
                    "redirect": next_target,
                    "user": {"login": username, "user_id": user_id}
                }, status=200, extra_headers={"Set-Cookie": cookie_hdr})
                return

            else:
                self.send_error(404, "Endpoint not found")
                return

        elif parsed.path.startswith("/api/"):
            params = urllib.parse.parse_qs(parsed.query)

            try:
                content_len = int(self.headers.get("Content-Length", 0))
            except (ValueError, TypeError):
                content_len = 0

            # Body size limit: 1 MB
            if content_len > MAX_BODY_SIZE:
                self.close_connection = True
                try:
                    remaining = content_len
                    while remaining > 0:
                        chunk = self.rfile.read(min(remaining, 65536))
                        if not chunk:
                            break
                        remaining -= len(chunk)
                except Exception:
                    pass
                self._send_json(
                    {"status": "error", "error_code": "PAYLOAD_TOO_LARGE", "message": "Payload too large: maximum body size is 1MB"},
                    status=413,
                    extra_headers={"Connection": "close"}
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

            # Check authorization before handling POST body
            ok, status_code, message = self.server.api_handler.check_authorization(
                "POST", parsed.path, headers_dict, client_ip, query_params=params, body_json=body_json
            )
            if not ok:
                self._send_json({"status": "error", "message": message}, status=status_code)
                return

            res = self.server.api_handler.handle_post(
                parsed.path, body_json, headers=headers_dict, client_ip=client_ip
            )
            status = res.get("status_code", 200 if res.get("status") == "success" else 400)
            self._send_json(res, status=status)
        else:
            self.send_error(404, "Endpoint not found")

    def do_DELETE(self):
        self._init_request_context()
        parsed = urllib.parse.urlparse(self.path)
        if not self._check_rate_limit(parsed.path):
            return
        client_ip = self.client_address[0]
        headers_dict = {k: v for k, v in self.headers.items()}

        # Enforce CSRF Origin check if authenticated via cookie
        csrf_ok, csrf_status, csrf_msg = enforce_csrf_for_cookie(headers_dict, parsed.path)
        if not csrf_ok:
            self._send_json({"status": "error", "message": csrf_msg}, status=csrf_status)
            return

        ok, status_code, message = self.server.api_handler.check_authorization(
            "DELETE", parsed.path, headers_dict, client_ip
        )
        if not ok:
            self._send_json({"status": "error", "message": message}, status=status_code)
            return

        res = self.server.api_handler.handle_delete(
            parsed.path, headers=headers_dict, client_ip=client_ip
        )
        status = res.get("status_code", 200 if res.get("status") == "success" else 400)
        self._send_json(res, status=status)

    def handle_one_request(self):
        try:
            super().handle_one_request()
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _send_json(self, data, status=200, extra_headers=None):
        try:
            req_id = getattr(self, "_request_id", None) or str(uuid.uuid4())
            if isinstance(data, dict) and "request_id" not in data and not getattr(self, "path", "").startswith("/api/auth-config"):
                data["request_id"] = req_id

            body = json.dumps(data, indent=2).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("X-Request-ID", req_id)

            if extra_headers:
                for k, v in extra_headers.items():
                    self.send_header(k, v)

            # CORS: Default same-origin only; echo origin only if in CIF_CORS_ORIGINS allowlist
            origin = self.headers.get("Origin") if hasattr(self, "headers") and self.headers else None
            allowed_origin = get_cors_origin(origin)
            if allowed_origin:
                self.send_header("Access-Control-Allow-Origin", allowed_origin)
                self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Hub-Signature-256, X-GitHub-Event, X-Request-ID")

            self.end_headers()
            self.wfile.write(body)

            start_time = getattr(self, "_start_time", None)
            latency_ms = round((time.time() - start_time) * 1000, 2) if start_time else 0.0
            client_ip = self.client_address[0] if hasattr(self, "client_address") else "-"
            api_logger.info(f"{self.command} {self.path} -> {status} ({latency_ms}ms) [client={client_ip}]")
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_OPTIONS(self):
        origin = self.headers.get("Origin") if hasattr(self, "headers") and self.headers else None
        allowed_origin = get_cors_origin(origin)
        if allowed_origin:
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", allowed_origin)
            self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Hub-Signature-256, X-GitHub-Event, X-Request-ID")
            self.end_headers()
        else:
            self.send_response(204)
            self.end_headers()

    def log_message(self, format, *args):
        server_logger.info("%s - " + format, self.address_string(), *args)


# Ensure stdout is utf-8 compatible on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def check_bind_safety(bind_host: str) -> None:
    if bind_host in ("0.0.0.0", "::"):
        print(f"[SECURITY] Bound to public interface {bind_host}. Ensure firewall is active.")

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
