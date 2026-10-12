"""
Privacy-First Ingestion Sanitizer (Step 5.1)
Redacts secrets, credentials, API keys, private keys, sensitive query parameters,
and optional PII (emails, phone numbers) before persistence, logging, or LLM transmission.
"""
import os
import re
import urllib.parse
import logging
from typing import Any, Dict, List, Optional, Tuple, Union
from backend.models import Event

# Secret Pattern Definitions (Regexes compiled for high-throughput scanning)
# Replacement tokens follow standard schema: [REDACTED:<type>]

# 1. GitHub Tokens
RE_GITHUB_TOKENS = re.compile(
    r"\b("
    r"ghp_[A-Za-z0-9_]{36,}|"
    r"gho_[A-Za-z0-9_]{36,}|"
    r"ghs_[A-Za-z0-9_]{36,}|"
    r"ghr_[A-Za-z0-9_]{36,}|"
    r"github_pat_[A-Za-z0-9_]{22,}"
    r")\b"
)

# 2. AWS Access Keys & Secret Keys
RE_AWS_KEY = re.compile(r"(?<![A-Z0-9])(AKIA[0-9A-Z]{16})(?![A-Z0-9])")
RE_AWS_SECRET = re.compile(
    r"(?i)\b(aws_secret_access_key|aws_secret_key)\s*([:=])\s*['\"]?([A-Za-z0-9/+=]{40})['\"]?"
)

# 3. Slack Tokens
RE_SLACK_TOKEN = re.compile(r"\b(xox[baprs]-[0-9A-Za-z\-]{10,})\b")

# 4. Google API Keys
RE_GOOGLE_KEY = re.compile(r"\b(AIza[0-9A-Za-z\-_]{35})\b")

# 5. Private Key Blocks
RE_PRIVATE_KEY = re.compile(
    r"-----BEGIN\s+[A-Z0-9\s_-]*PRIVATE\s+KEY-----[\s\S]*?-----END\s+[A-Z0-9\s_-]*PRIVATE\s+KEY-----",
    re.MULTILINE
)

# 6. JSON Web Tokens (JWT)
RE_JWT = re.compile(r"\b(eyJ[A-Za-z0-9\-_]{10,}\.eyJ[A-Za-z0-9\-_]{10,}\.[A-Za-z0-9\-_]{10,})\b")

# 7. Bearer Tokens & Authorization Headers
RE_BEARER = re.compile(r"(?i)\b(?:Authorization:\s*)?Bearer\s+([A-Za-z0-9\-_.~+/]{16,}=*)")

# 8. Secret / Password Assignments (negative lookahead prevents double-redacting [REDACTED:...])
RE_SECRET_ASSIGNMENT = re.compile(
    r"(?i)\b(password|passwd|secret|token|api_key|access_key|client_secret|auth_token|api[_-]?secret|private[_-]?key|secret[_-]?key|key)\s*([:=]|\s+)\s*(['\"]?)(?!\[REDACTED:)([^\s'\",;]{4,})\3"
)

# 9. Optional PII (Enabled when CIF_REDACT_PII=1)
RE_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
RE_PHONE = re.compile(r"(?:\+?[0-9]{1,3}[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b")

# URL Credential Pattern
RE_URL_CREDENTIALS = re.compile(r"://([^:]+):([^@]+)@")


def is_pii_redaction_enabled() -> bool:
    """Returns True if PII redaction is requested via CIF_REDACT_PII=1."""
    return os.environ.get("CIF_REDACT_PII", "0").lower() in ("1", "true", "yes")


def is_author_redaction_enabled() -> bool:
    """Returns True if author redaction is requested via CIF_REDACT_AUTHOR=1 or CIF_REDACT_PII=1."""
    return os.environ.get("CIF_REDACT_AUTHOR", "0").lower() in ("1", "true", "yes") or is_pii_redaction_enabled()


def sanitize_text(text: Optional[str]) -> str:
    """Redacts all sensitive patterns from a text string with standard replacement tokens."""
    if not text:
        return ""
    
    # 1. Private Keys
    text = RE_PRIVATE_KEY.sub("[REDACTED:PRIVATE_KEY]", text)

    # 2. GitHub Tokens
    text = RE_GITHUB_TOKENS.sub("[REDACTED:GITHUB_TOKEN]", text)

    # 3. AWS Keys & Secrets
    text = RE_AWS_SECRET.sub(r"\1\2[REDACTED:AWS_SECRET]", text)
    text = RE_AWS_KEY.sub("[REDACTED:AWS_KEY]", text)

    # 4. Slack Tokens
    text = RE_SLACK_TOKEN.sub("[REDACTED:SLACK_TOKEN]", text)

    # 5. Google API Keys
    text = RE_GOOGLE_KEY.sub("[REDACTED:GOOGLE_KEY]", text)

    # 6. JWTs
    text = RE_JWT.sub("[REDACTED:JWT]", text)

    # 7. Bearer Tokens
    text = RE_BEARER.sub("Bearer [REDACTED:BEARER_TOKEN]", text)

    # 8. Secret / Password Assignments
    text = RE_SECRET_ASSIGNMENT.sub(r"\1\2\3[REDACTED:SECRET_ASSIGNMENT]\3", text)

    # 9. Optional PII
    if is_pii_redaction_enabled():
        text = RE_EMAIL.sub("[REDACTED:EMAIL]", text)
        text = RE_PHONE.sub("[REDACTED:PHONE]", text)

    return text


def sanitize_url(url: Optional[str]) -> str:
    """
    Sanitizes URL by removing basic auth credentials and redacting query parameter values.
    Example:
      https://user:pass@host.com/path?token=secret&id=123
      -> https://[REDACTED:CREDENTIALS]@host.com/path?token=[REDACTED:QUERY_PARAM]&id=[REDACTED:QUERY_PARAM]
    """
    if not url:
        return ""

    # Redact embedded HTTP Basic credentials
    url = RE_URL_CREDENTIALS.sub("://[REDACTED:CREDENTIALS]@", url)

    try:
        parsed = urllib.parse.urlsplit(url)
        if parsed.query:
            # Redact parameter values while keeping query structure
            query_pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
            redacted_pairs = []
            for k, v in query_pairs:
                if v:
                    redacted_pairs.append((k, "[REDACTED:QUERY_PARAM]"))
                else:
                    redacted_pairs.append((k, v))
            new_query = urllib.parse.urlencode(redacted_pairs)
            parsed = parsed._replace(query=new_query)
            url = urllib.parse.urlunsplit(parsed)
    except Exception:
        # Fallback regex redaction if URL parsing encounters atypical characters
        url = re.sub(r"([?&][^=]+)=([^&#]*)", r"\1=[REDACTED:QUERY_PARAM]", url)

    # Also pass through general text sanitizer for any tokens in path/fragment
    return sanitize_text(url)


def sanitize_author(author: Optional[str]) -> str:
    """Sanitizes author identity string."""
    if not author:
        return ""
    if is_author_redaction_enabled():
        return "[REDACTED:AUTHOR]"
    # Always sanitize against tokens/emails
    return sanitize_text(author)


def sanitize_metadata(data: Any) -> Any:
    """Recursively traverses dictionary or list and sanitizes all string values."""
    if isinstance(data, dict):
        sanitized_dict = {}
        for k, v in data.items():
            # If the dictionary key itself suggests a credential, sanitize the value directly
            k_str = str(k).lower()
            if any(term in k_str for term in ("password", "passwd", "secret", "token", "api_key", "access_key")):
                sanitized_dict[k] = "[REDACTED:SECRET_ASSIGNMENT]"
            else:
                sanitized_dict[k] = sanitize_metadata(v)
        return sanitized_dict
    elif isinstance(data, list):
        return [sanitize_metadata(item) for item in data]
    elif isinstance(data, str):
        return sanitize_text(data)
    else:
        return data


def sanitize_event(event: Event) -> Event:
    """
    Redacts all confidential information in an Event before persistence, logging, or indexing.
    Modifies in-place and returns the sanitized event.
    """
    if not event:
        return event

    event.title = sanitize_text(event.title) if event.title else ""
    event.body = sanitize_text(event.body) if event.body else ""
    event.source_url = sanitize_url(event.source_url) if event.source_url else ""
    event.author = sanitize_author(event.author) if event.author else ""
    if event.raw_metadata:
        event.raw_metadata = sanitize_metadata(event.raw_metadata)

    return event


class SanitizingLogFilter(logging.Filter):
    """Logging filter that scrubs sensitive patterns from all log records and exception messages."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = sanitize_text(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: sanitize_text(str(v)) for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(sanitize_text(str(v)) for v in record.args)
        if record.exc_text:
            record.exc_text = sanitize_text(record.exc_text)
        return True


def install_sanitizing_logger(logger: Optional[logging.Logger] = None) -> None:
    """Attaches SanitizingLogFilter to the specified logger or root logger."""
    target_logger = logger or logging.getLogger()
    for existing_filter in target_logger.filters:
        if isinstance(existing_filter, SanitizingLogFilter):
            return
    target_logger.addFilter(SanitizingLogFilter())
