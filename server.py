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
import hmac
import http.server
import json
import os
import sys
import time
import urllib.parse
import uuid
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


LOOPBACK_HOSTS = ("127.0.0.1", "localhost", "::1")


def check_bind_safety(host: str) -> None:
    """Refuses to expose a dev-mode server beyond loopback (audit fix SEC-06).

    In dev mode every loopback caller is treated as an administrator. Behind a reverse proxy
    or port-forward running on the same machine, *every* remote visitor would appear to come
    from 127.0.0.1 — so a dev-mode server must never listen on a public interface.
    (Previously a second, print-only definition of this function silently replaced this check.)
    """
    if host in LOOPBACK_HOSTS:
        return
    if os.environ.get("CIF_DEV_MODE", "0").strip() == "1":
        raise SystemExit(
            f"Security Error: refusing to bind on '{host}' while CIF_DEV_MODE=1. "
            "Dev mode grants admin rights to loopback callers; bind to 127.0.0.1 or disable dev mode."
        )
    print(f"[SECURITY] Listening on public interface {host}. Use HTTPS and a firewall in production.")


def _same_origin_ok(origin: str, host_header: str = "") -> bool:
    """True when `origin` is this server's own origin or an explicitly allow-listed one.

    "Own origin" means either CIF_BASE_URL or the Host the request was actually sent to, so the
    server works on any port without extra configuration. A cross-site page cannot make its
    Origin equal the victim server's Host; DNS-rebinding (attacker domain pointed at 127.0.0.1)
    is refused by the dev-mode Host check, and without dev mode such a page has no session cookie.
    """
    from backend.auth.sessions import validate_csrf_origin
    from backend.config import get_config
    if validate_csrf_origin(origin, get_config().get_base_url()):
        return True
    netloc = urllib.parse.urlparse(origin).netloc.lower()
    if host_header and netloc and netloc == host_header.strip().lower():
        return True
    return get_cors_origin(origin) is not None


class ContextIntelligenceServer(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def _init_request_context(self):
        self._start_time = time.time()
        self._request_id = self.headers.get("X-Request-ID") or str(uuid.uuid4())
        set_request_id(self._request_id)

    def _get_client_key(self) -> str:
        """Rate-limit bucket key (audit fix SEC-05).

        A per-user bucket is used only when the presented credential is a *valid* session or
        the admin token. Previously any string in the Authorization header or cookie got its
        own bucket, so rotating fake tokens bypassed the limit entirely.
        """
        client_ip = self.client_address[0] if hasattr(self, "client_address") else "127.0.0.1"
        try:
            from backend.auth.sessions import extract_session_token, get_session
            headers_dict = {k: v for k, v in self.headers.items()}
            token, _ = extract_session_token(headers_dict)
            if token:
                admin_token = os.environ.get("CIF_ADMIN_TOKEN", "").strip()
                if admin_token and hmac.compare_digest(token.encode(), admin_token.encode()):
                    return "user:admin"
                session = get_session(self.server.api_handler.db, token)
                if session:
                    return f"user:{session['user_id']}"
        except Exception:
            server_logger.exception("Rate-limit key lookup failed; falling back to client IP")
        return f"ip:{client_ip}"

    def _reject(self, status: int, error_code: str, message: str) -> bool:
        self._send_json({"status": "error", "error_code": error_code, "message": message}, status=status)
        return False

    def _guard_request(self, parsed_path: str) -> bool:
        """Host / CSRF / content-type checks for /api and /auth requests (audit fix SEC-02).

        1. DNS-rebinding: in dev mode loopback callers are admins, so the Host header must be a
           loopback name too (an attacker domain re-pointed at 127.0.0.1 is refused).
        2. CSRF: a state-changing request authenticated *ambiently* (session cookie or dev-mode
           IP) must come from this site. Requests carrying an Authorization header cannot be
           forged cross-site without a CORS preflight, which this server never grants to
           unknown origins, so they are exempt.
        3. A non-empty POST body must be declared application/json, which turns every cross-site
           write into a preflighted request (closes the text/plain "simple request" vector).
        """
        if not (parsed_path.startswith("/api/") or parsed_path.startswith("/auth/")):
            return True
        if os.environ.get("CIF_DEV_MODE", "0").strip() == "1":
            host = (self.headers.get("Host") or "").strip().lower()
            hostname = host.rsplit(":", 1)[0] if not host.startswith("[") else host.split("]")[0] + "]"
            if hostname not in ("127.0.0.1", "localhost", "[::1]", "::1"):
                return self._reject(403, "HOST_NOT_ALLOWED",
                                    "Dev mode only accepts requests addressed to localhost")
        if self.command in ("POST", "PUT", "PATCH", "DELETE"):
            if parsed_path == "/api/webhook/github":
                return True  # authenticated by HMAC signature, not ambient credentials
            if not self.headers.get("Authorization"):
                origin = self.headers.get("Origin")
                if not origin and self.headers.get("Referer"):
                    ref = urllib.parse.urlparse(self.headers.get("Referer"))
                    origin = f"{ref.scheme}://{ref.netloc}"
                if origin and not _same_origin_ok(origin, self.headers.get("Host") or ""):
                    return self._reject(403, "CSRF_ORIGIN_MISMATCH",
                                        "Cross-site request refused: Origin does not match this server")
                if not origin and "cif_session=" in (self.headers.get("Cookie") or ""):
                    # Browsers always send Origin on fetch/form POSTs; a cookie without it is suspect.
                    return self._reject(403, "CSRF_ORIGIN_MISSING",
                                        "Cookie-authenticated requests must include an Origin header")
            try:
                content_len = int(self.headers.get("Content-Length", 0) or 0)
            except ValueError:
                content_len = 0
            ctype = (self.headers.get("Content-Type") or "").split(";")[0].strip().lower()
            # (Bodies over the limit fall through to the 413 handler, which drains them.)
            if self.command == "POST" and 0 < content_len <= MAX_BODY_SIZE and ctype != "application/json":
                return self._reject(415, "UNSUPPORTED_MEDIA_TYPE",
                                    "Request body must be JSON (Content-Type: application/json)")
        return True

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

    def _safe_dispatch(self, handler):
        """Runs a request handler; any unexpected exception becomes a JSON 500 (audit fix APP-02).

        Previously an exception escaped into http.server, which closed the connection without a
        status line, so the browser saw an empty reply and the frontend silently fell back to
        mock data. The traceback is logged server-side only; the client gets the request id.
        """
        self._init_request_context()
        try:
            handler()
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception:
            server_logger.exception("Unhandled error while serving %s %s", self.command, self.path)
            try:
                self._send_json({
                    "status": "error",
                    "error_code": "INTERNAL_ERROR",
                    "message": "Internal server error. Quote the request_id when reporting this problem.",
                }, status=500)
            except Exception:
                pass

    def do_GET(self):
        self._safe_dispatch(self._handle_GET)

    def _handle_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if not self._check_rate_limit(parsed.path):
            return
        if not self._guard_request(parsed.path):
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
                # Shared, password-less demo account (no admin rights). Can be switched off
                # with CIF_DEMO_LOGIN=0. Audit fix SEC-04: `next` is validated so this endpoint
                # can no longer be used as an open redirect to another site.
                if os.environ.get("CIF_DEMO_LOGIN", "1").strip() == "0":
                    self._send_json({"status": "error", "error_code": "DEMO_LOGIN_DISABLED",
                                     "message": "Demo login is disabled on this server"}, status=403)
                    return
                from backend.auth.github_login import validate_next_path
                try:
                    next_path = validate_next_path(params.get("next", ["/dashboard.html"])[0])
                except ValueError:
                    next_path = "/dashboard.html"
                now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
                with self.server.api_handler.db.get_connection() as conn:
                    user_row = conn.execute("SELECT user_id FROM users WHERE login = 'demo-developer'").fetchone()
                    if user_row:
                        user_id = user_row["user_id"]
                        conn.execute("UPDATE users SET last_login_at = ? WHERE user_id = ?", (now_str, user_id))
                    else:
                        # Negative github_id: can never collide with a real GitHub account id.
                        lowest = conn.execute("SELECT MIN(github_id) FROM users").fetchone()[0]
                        demo_gh_id = min(int(lowest or 0), 0) - 1
                        cur = conn.execute("""
                        INSERT INTO users (github_id, login, avatar_url, created_at, last_login_at)
                        VALUES (?, ?, '', ?, ?)
                        """, (demo_gh_id, "demo-developer", now_str, now_str))
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
        self._safe_dispatch(self._handle_POST)

    def _handle_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if not self._check_rate_limit(parsed.path):
            return
        if not self._guard_request(parsed.path):
            return
        params = urllib.parse.parse_qs(parsed.query)
        headers_dict = {k: v for k, v in self.headers.items()}
        client_ip = self.client_address[0] if self.client_address else "127.0.0.1"

        # CSRF / content-type checks are done for every state-changing request in _guard_request.
        from backend.auth.sessions import extract_session_token

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
            except (ValueError, UnicodeDecodeError):
                self._send_json({"status": "error", "error_code": "INVALID_JSON",
                                 "message": "Invalid JSON in request body"}, status=400)
                return
            if not isinstance(body_json, dict):
                self._send_json({"status": "error", "error_code": "INVALID_JSON",
                                 "message": "Invalid JSON: body must be an object"}, status=400)
                return

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
                # Audit fix SEC-01: real username + password verification (backend/auth/local_accounts.py).
                from backend.auth.local_accounts import (
                    AccountError, authenticate_local_user, register_local_user)
                username = body_json.get("username") or body_json.get("login")
                password = body_json.get("password")
                is_register = parsed.path.endswith("/register")
                try:
                    if is_register:
                        account = register_local_user(self.server.api_handler.db, username, password)
                    else:
                        account = authenticate_local_user(self.server.api_handler.db, username, password)
                except AccountError as err:
                    if err.status == 401:
                        server_logger.warning("Failed local sign-in attempt from %s", self.client_address[0])
                    self._send_json({"status": "error", "error_code": "AUTH_FAILED" if err.status == 401
                                     else "INVALID_ACCOUNT_REQUEST", "message": err.message}, status=err.status)
                    return
                user_id = account["user_id"]
                username = account["login"]

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
        self._safe_dispatch(self._handle_DELETE)

    def _handle_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        if not self._check_rate_limit(parsed.path):
            return
        if not self._guard_request(parsed.path):
            return
        client_ip = self.client_address[0]
        headers_dict = {k: v for k, v in self.headers.items()}

        # Audit fix APP-01: this used to call an undefined `enforce_csrf_for_cookie`, so every
        # DELETE raised NameError. The CSRF check now happens in _guard_request (above).

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

    def end_headers(self):
        # (Previously defined twice; the first definition with these cache headers was dead code.)
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path.endswith((".html", ".css", ".js")) or parsed.path in ("", "/"):
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "same-origin")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https://avatars.githubusercontent.com; "
            "connect-src 'self' https://api.github.com;"
        )
        super().end_headers()

    def log_message(self, format, *args):
        server_logger.info("%s - " + format, self.address_string(), *args)


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
