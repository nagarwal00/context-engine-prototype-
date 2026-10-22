"""
Hardened GitHub API Client (Step 7.6)
Implements:
1. Secure TLS context with strict certificate verification; pinned API version header.
2. Manual redirect following with Authorization header stripping on cross-host redirects.
3. Link header pagination with per_page=100.
4. Rate limit awareness (X-RateLimit-Remaining/Reset, Retry-After) with backoff.
5. Conditional requests via ETag / If-None-Match (304 Not Modified support).
6. Timeouts (30s) and 5xx retries with exponential backoff; never weakens TLS.
7. Tokens strictly kept in memory; sanitized error messages.
"""
import datetime
import json
import logging
import os
import re
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable, Dict, Generator, List, Optional, Tuple, Union

from backend.ingestion.sanitizer import sanitize_text

logger = logging.getLogger("cif.ingestion.github_client")

GITHUB_API_VERSION = "2022-11-28"
DEFAULT_TIMEOUT = 30
MAX_5XX_RETRIES = 3
RE_LINK_NEXT = re.compile(r'<([^>]+)>;\s*rel="next"')


class GitHubClientError(Exception):
    """Base exception for hardened GitHub client."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(sanitize_text(message))
        self.status_code = status_code


class GitHubTLSError(GitHubClientError):
    """Raised on TLS certificate verification failures. Must never be retried with weaker settings."""
    pass


class GitHubRateLimitError(GitHubClientError):
    """Raised when rate limit is exceeded and backoff cannot resolve it."""
    def __init__(self, message: str, reset_timestamp: Optional[float] = None):
        super().__init__(message, status_code=429)
        self.reset_timestamp = reset_timestamp


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Disables urllib's automatic redirect following to prevent Authorization header leaks."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def get_secure_ssl_context() -> ssl.SSLContext:
    """Returns strict default SSL context or custom CA bundle if CIF_CA_BUNDLE is configured."""
    ca_bundle = os.environ.get("CIF_CA_BUNDLE")
    if ca_bundle and os.path.exists(ca_bundle):
        return ssl.create_default_context(cafile=ca_bundle)
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        pass
    return ssl.create_default_context()


class HardenedGitHubClient:
    """
    Hardened GitHub REST API client designed for automated repository ingestion.
    """
    def __init__(
        self,
        token: Optional[str] = None,
        ssl_context: Optional[ssl.SSLContext] = None,
        rate_limit_callback: Optional[Callable[[str, int], None]] = None,
        max_rate_limit_wait: int = 120
    ):
        self._token = token.strip() if token and str(token).strip() else None
        self._ssl_context = ssl_context or get_secure_ssl_context()
        self._rate_limit_callback = rate_limit_callback
        self._max_rate_limit_wait = max_rate_limit_wait
        self._opener = urllib.request.build_opener(NoRedirectHandler)

    @property
    def has_token(self) -> bool:
        return bool(self._token)

    def request(
        self,
        url: str,
        method: str = "GET",
        data: Optional[Union[Dict[str, Any], bytes]] = None,
        headers: Optional[Dict[str, str]] = None,
        etag: Optional[str] = None,
        stream: bool = False
    ) -> Tuple[int, Any, Dict[str, str]]:
        """
        Executes a single HTTP request with manual redirect following, retry on 5xx,
        and header stripping on cross-host redirects.
        Returns (status_code, parsed_data_or_bytes, response_headers).
        """
        cur_url = url
        cur_headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
            "User-Agent": "CIF-Ingestor/1.0",
        }
        if headers:
            cur_headers.update(headers)

        if self._token:
            cur_headers["Authorization"] = f"Bearer {self._token}"

        if etag:
            cur_headers["If-None-Match"] = etag

        req_body = None
        if data is not None:
            if isinstance(data, (dict, list)):
                req_body = json.dumps(data).encode("utf-8")
                cur_headers["Content-Type"] = "application/json"
            elif isinstance(data, bytes):
                req_body = data

        redirect_count = 0
        max_redirects = 5

        while redirect_count <= max_redirects:
            status, resp_data, resp_headers = self._execute_with_retries(
                cur_url, method, req_body, cur_headers, stream
            )

            # Check 304 Not Modified
            if status == 304:
                return 304, None, resp_headers

            # Handle redirects manually (301, 302, 303, 307, 308)
            if status in (301, 302, 303, 307, 308) and "Location" in resp_headers:
                redirect_count += 1
                new_url = resp_headers["Location"]
                parsed_old = urllib.parse.urlparse(cur_url)
                parsed_new = urllib.parse.urlparse(new_url)

                # Rule 2: Strip Authorization header when host changes
                if parsed_new.netloc.lower() != parsed_old.netloc.lower():
                    cur_headers.pop("Authorization", None)

                # 303 requires GET method change
                if status == 303:
                    method = "GET"
                    req_body = None

                cur_url = new_url
                continue

            return status, resp_data, resp_headers

        raise GitHubClientError(f"Exceeded maximum redirects ({max_redirects}) for {cur_url}")

    def _execute_with_retries(
        self,
        url: str,
        method: str,
        body: Optional[bytes],
        headers: Dict[str, str],
        stream: bool = False
    ) -> Tuple[int, Any, Dict[str, str]]:
        """Executes request with 5xx retry backoff and rate limit handling."""
        attempt = 0
        backoff = 1.0

        while attempt < MAX_5XX_RETRIES:
            attempt += 1
            req = urllib.request.Request(url, data=body, headers=headers, method=method)

            try:
                with self._opener.open(req, timeout=DEFAULT_TIMEOUT) as resp:
                    status = resp.getcode()
                    resp_headers = dict(resp.headers)
                    raw = resp.read()
                    data = self._parse_body(raw, resp_headers) if not stream else raw
                    return status, data, resp_headers

            except urllib.error.HTTPError as e:
                status = e.code
                resp_headers = dict(e.headers)

                # 304 Not Modified or redirect codes
                if status in (304, 301, 302, 303, 307, 308):
                    raw = e.read()
                    return status, None, resp_headers

                # Handle Rate Limiting (429 or 403 with 0 remaining)
                remaining = resp_headers.get("X-RateLimit-Remaining")
                is_rate_limited = status == 429 or (status == 403 and remaining == "0")
                if is_rate_limited:
                    wait_seconds = self._calc_rate_limit_wait(resp_headers)
                    if wait_seconds > 0 and wait_seconds <= self._max_rate_limit_wait:
                        msg = f"Waiting for rate limit: {wait_seconds:.1f}s"
                        if self._rate_limit_callback:
                            self._rate_limit_callback(msg, int(wait_seconds))
                        time.sleep(wait_seconds)
                        continue  # Retry after waiting
                    else:
                        raise GitHubRateLimitError(
                            f"GitHub rate limit exceeded. Reset in {wait_seconds:.1f}s",
                            reset_timestamp=time.time() + wait_seconds
                        )

                # 5xx server errors: retry with exponential backoff
                if 500 <= status < 600 and attempt < MAX_5XX_RETRIES:
                    time.sleep(backoff)
                    backoff *= 2.0
                    continue

                raw = e.read()
                data = self._parse_body(raw, resp_headers)
                return status, data, resp_headers

            except (ssl.SSLError, ssl.CertificateError) as ssl_err:
                # Rule 6: Never retry TLS errors with weaker settings
                raise GitHubTLSError(f"TLS certificate verification failed: {ssl_err}") from ssl_err

            except (urllib.error.URLError, TimeoutError, OSError) as net_err:
                if attempt < MAX_5XX_RETRIES:
                    time.sleep(backoff)
                    backoff *= 2.0
                    continue
                raise GitHubClientError(f"Network error accessing {url}: {net_err}") from net_err

        raise GitHubClientError(f"Request failed after {MAX_5XX_RETRIES} attempts to {url}")

    def _calc_rate_limit_wait(self, headers: Dict[str, str]) -> float:
        """Determines required wait seconds from Retry-After or X-RateLimit-Reset headers."""
        if "Retry-After" in headers:
            try:
                return float(headers["Retry-After"])
            except ValueError:
                pass

        if "X-RateLimit-Reset" in headers:
            try:
                reset_ts = float(headers["X-RateLimit-Reset"])
                now = time.time()
                diff = reset_ts - now
                return max(1.0, min(diff + 1.0, 3600.0))
            except ValueError:
                pass

        return 5.0

    def _parse_body(self, raw_bytes: bytes, headers: Dict[str, str]) -> Any:
        if not raw_bytes:
            return None
        content_type = headers.get("Content-Type", "")
        if "application/json" in content_type:
            try:
                return json.loads(raw_bytes.decode("utf-8"))
            except Exception:
                return raw_bytes.decode("utf-8", errors="replace")
        return raw_bytes.decode("utf-8", errors="replace")

    def paginate(
        self,
        url: str,
        max_items: Optional[int] = None,
        params: Optional[Dict[str, Any]] = None,
        on_page: Optional[Callable[[int, int], None]] = None,
        start_page: int = 1
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Yields items one by one across paginated GitHub endpoints using per_page=100 and Link headers.
        Respects max_items limit if supplied.
        """
        cur_url = url
        parsed = urllib.parse.urlparse(cur_url)
        q = urllib.parse.parse_qs(parsed.query)

        # Force per_page=100 per Rule 3
        q["per_page"] = ["100"]
        if start_page > 1:
            q["page"] = [str(start_page)]
        if params:
            for k, v in params.items():
                q[k] = [str(v)]

        new_query = urllib.parse.urlencode(q, doseq=True)
        cur_url = urllib.parse.urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))

        yielded_count = 0
        page_num = start_page

        while cur_url:
            status, data, resp_headers = self.request(cur_url)
            if status == 304:
                return
            if status != 200:
                raise GitHubClientError(f"Pagination error on {cur_url}: HTTP {status} {data}", status_code=status)

            items = data if isinstance(data, list) else data.get("items", []) if isinstance(data, dict) else []
            for item in items:
                if isinstance(item, dict):
                    yield item
                    yielded_count += 1
                    if max_items and yielded_count >= max_items:
                        return

            if on_page:
                on_page(page_num, yielded_count)

            # Extract next link from Link header
            link_header = resp_headers.get("Link", "")
            match = RE_LINK_NEXT.search(link_header)
            if match:
                cur_url = match.group(1)
                page_num += 1
            else:
                break

    def fetch_tarball_stream(
        self,
        tarball_url: str,
        max_mb: int = 100
    ) -> Tuple[bool, Optional[bytes], str]:
        """
        Downloads default branch tarball with host-redirect authorization stripping.
        Returns (success_bool, tarball_bytes_or_None, reason_string).
        """
        max_bytes = max_mb * 1024 * 1024
        try:
            status, raw_bytes, _ = self.request(tarball_url, stream=True)
            if status != 200 or not raw_bytes:
                return False, None, f"Failed to download tarball: HTTP {status}"

            if len(raw_bytes) > max_bytes:
                return False, None, f"Tarball size ({len(raw_bytes)/(1024*1024):.1f}MB) exceeds cap of {max_mb}MB"

            return True, raw_bytes, "ok"
        except Exception as e:
            return False, None, f"Tarball download failed: {sanitize_text(str(e))}"
