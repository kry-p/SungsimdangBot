import json
import re
import traceback
from collections.abc import Iterable
from typing import Any

_MAX_EXCEPTION_MESSAGE_LENGTH = 300
_MAX_TRACEBACK_LENGTH = 8000
_API_KEY_PATTERN = re.compile(r"\bsk-[A-Za-z0-9_-]+\b")
_BEARER_TOKEN_PATTERN = re.compile(r"(?i)\bBearer\s+\S+")


def _sanitize_text(text: str, sensitive_values: Iterable[str | None]) -> str:
    safe_sensitive_values = (value for value in sensitive_values if isinstance(value, str) and value)
    for value in sorted(safe_sensitive_values, key=len, reverse=True):
        text = text.replace(value, "[REDACTED]")
    text = _API_KEY_PATTERN.sub("[REDACTED_API_KEY]", text)
    return _BEARER_TOKEN_PATTERN.sub("Bearer [REDACTED]", text)


def sanitize_exception_message(error: BaseException, sensitive_values: Iterable[str | None] = ()) -> str:
    message = " ".join(str(error).splitlines())
    return _sanitize_text(message, sensitive_values)[:_MAX_EXCEPTION_MESSAGE_LENGTH]


def sanitize_traceback(error: BaseException, sensitive_values: Iterable[str | None] = ()) -> str:
    traceback_text = "".join(traceback.TracebackException.from_exception(error, capture_locals=False).format())
    return _sanitize_text(traceback_text, sensitive_values)[:_MAX_TRACEBACK_LENGTH]


def build_diagnostic_event(event: str, message: str, **fields: Any) -> str:
    payload = {"event": event, "message": message}
    payload.update({key: value for key, value in fields.items() if value is not None})
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), default=str)
