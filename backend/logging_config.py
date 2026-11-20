"""
Centralized Structured Logging Configuration for Context Intelligence Framework (CIF)
Provides rotating file handlers for application, API, errors, database, security, and rate limiting.
Ensures console output is clear, human-readable, and sensitive secrets (tokens, keys) are masked.
"""
import os
import re
import sys
import logging
from logging.handlers import RotatingFileHandler
import threading
from typing import Optional

# Base directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# Thread-local storage for Request Correlation IDs
_thread_locals = threading.local()

def set_request_id(request_id: str) -> None:
    """Assign request ID to current thread context."""
    _thread_locals.request_id = request_id

def get_request_id() -> str:
    """Retrieve current thread request ID, or '-' if none set."""
    return getattr(_thread_locals, "request_id", "-")

class RequestIdFilter(logging.Filter):
    """Injects request_id into every LogRecord."""
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id") or record.request_id is None:
            record.request_id = get_request_id()
        return True

class SecretRedactionFilter(logging.Filter):
    """
    Scans log messages and redacts GitHub Personal Access Tokens, Bearer tokens,
    session secrets, and sensitive query parameters to prevent leakage.
    """
    TOKEN_PATTERNS = [
        # GitHub Personal Access Tokens (classic and fine-grained)
        (re.compile(r'(ghp_[a-zA-Z0-9]{36,}|gho_[a-zA-Z0-9]{36,}|github_pat_[a-zA-Z0-9_]{40,})'), r'[REDACTED_GH_TOKEN]'),
        # Bearer tokens in Authorization headers
        (re.compile(r'(Bearer\s+)[a-zA-Z0-9_\-\.]{8,}', re.IGNORECASE), r'\1[REDACTED_TOKEN]'),
        # Session tokens
        (re.compile(r'(cif_session=)[a-zA-Z0-9_\-\.]{12,}', re.IGNORECASE), r'\1[REDACTED_SESSION]'),
        # API Keys or secrets in parameters
        (re.compile(r'((?:key|secret|token|password)=)[^&\s]{6,}', re.IGNORECASE), r'\1[REDACTED]'),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            msg = record.msg
            for pattern, repl in self.TOKEN_PATTERNS:
                msg = pattern.sub(repl, msg)
            record.msg = msg
        return True

_LOGGING_INITIALIZED = False
_LOGGING_LOCK = threading.Lock()

def setup_logging(log_level: int = logging.INFO) -> None:
    """
    Initializes rotating file handlers and formatted console output.
    Idempotent and thread-safe.
    """
    global _LOGGING_INITIALIZED
    with _LOGGING_LOCK:
        if _LOGGING_INITIALIZED:
            return

        os.makedirs(LOGS_DIR, exist_ok=True)

        req_filter = RequestIdFilter()
        redact_filter = SecretRedactionFilter()

        # Formatters
        file_formatter = logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)s] [%(name)s] [%(request_id)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_formatter = logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)-5s] [%(request_id)s] %(message)s",
            datefmt="%H:%M:%S"
        )

        max_bytes = 5 * 1024 * 1024  # 5 MB per file
        backup_count = 5

        # 1. Root / Application Log Handler (application.log)
        app_file_handler = RotatingFileHandler(
            os.path.join(LOGS_DIR, "application.log"),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8"
        )
        app_file_handler.setLevel(log_level)
        app_file_handler.setFormatter(file_formatter)
        app_file_handler.addFilter(req_filter)
        app_file_handler.addFilter(redact_filter)

        # 2. API Request Log Handler (api.log)
        api_file_handler = RotatingFileHandler(
            os.path.join(LOGS_DIR, "api.log"),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8"
        )
        api_file_handler.setLevel(logging.INFO)
        api_file_handler.setFormatter(file_formatter)
        api_file_handler.addFilter(req_filter)
        api_file_handler.addFilter(redact_filter)

        # 3. Error Log Handler (error.log - WARNING and above)
        err_file_handler = RotatingFileHandler(
            os.path.join(LOGS_DIR, "error.log"),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8"
        )
        err_file_handler.setLevel(logging.WARNING)
        err_file_handler.setFormatter(file_formatter)
        err_file_handler.addFilter(req_filter)
        err_file_handler.addFilter(redact_filter)

        # 4. Database Log Handler (database.log)
        db_file_handler = RotatingFileHandler(
            os.path.join(LOGS_DIR, "database.log"),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8"
        )
        db_file_handler.setLevel(logging.INFO)
        db_file_handler.setFormatter(file_formatter)
        db_file_handler.addFilter(req_filter)
        db_file_handler.addFilter(redact_filter)

        # 5. Security Log Handler (security.log)
        sec_file_handler = RotatingFileHandler(
            os.path.join(LOGS_DIR, "security.log"),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8"
        )
        sec_file_handler.setLevel(logging.INFO)
        sec_file_handler.setFormatter(file_formatter)
        sec_file_handler.addFilter(req_filter)
        sec_file_handler.addFilter(redact_filter)

        # 6. Rate Limiting Log Handler (rate_limit.log)
        rl_file_handler = RotatingFileHandler(
            os.path.join(LOGS_DIR, "rate_limit.log"),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8"
        )
        rl_file_handler.setLevel(logging.INFO)
        rl_file_handler.setFormatter(file_formatter)
        rl_file_handler.addFilter(req_filter)
        rl_file_handler.addFilter(redact_filter)

        # 7. Console Stream Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(console_formatter)
        console_handler.addFilter(req_filter)
        console_handler.addFilter(redact_filter)

        # Attach to root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        root_logger.addHandler(app_file_handler)
        root_logger.addHandler(err_file_handler)
        root_logger.addHandler(console_handler)

        # Attach specialized loggers
        api_logger = logging.getLogger("cif.api")
        api_logger.addHandler(api_file_handler)

        server_logger = logging.getLogger("cif.server")
        server_logger.addHandler(api_file_handler)

        db_logger = logging.getLogger("cif.database")
        db_logger.addHandler(db_file_handler)

        sec_logger = logging.getLogger("cif.security")
        sec_logger.addHandler(sec_file_handler)

        rl_logger = logging.getLogger("cif.rate_limit")
        rl_logger.addHandler(rl_file_handler)

        _LOGGING_INITIALIZED = True
        root_logger.info("Context Intelligence Framework structured logging system initialized.")

def get_logger(name: str = "cif") -> logging.Logger:
    """Returns a named logger configured within the CIF hierarchy."""
    if not _LOGGING_INITIALIZED:
        setup_logging()
    return logging.getLogger(name)

