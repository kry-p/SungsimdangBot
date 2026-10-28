import json
import re
from collections.abc import Iterable
from typing import Any

_MAX_EXCEPTION_MESSAGE_LENGTH = 300
_API_KEY_PATTERN = re.compile(r"\bsk-[A-Za-z0-9_-]+\b")
_BEARER_TOKEN_PATTERN = re.compile(r"(?i)\bBearer\s+\S+")


def sanitize_exception_message(error: BaseException, sensitive_values: Iterable[str | None] = ()) -> str:
    message = " ".join(str(error).splitlines())
    safe_sensitive_values = (value for value in sensitive_values if isinstance(value, str) and value)
    for value in sorted(safe_sensitive_values, key=len, reverse=True):
        message = message.replace(value, "[REDACTED]")
    message = _API_KEY_PATTERN.sub("[REDACTED_API_KEY]", message)
    message = _BEARER_TOKEN_PATTERN.sub("Bearer [REDACTED]", message)
    return message[:_MAX_EXCEPTION_MESSAGE_LENGTH]


def build_diagnostic_event(event: str, message: str, **fields: Any) -> str:
    payload = {"event": event, "message": message}
    payload.update({key: value for key, value in fields.items() if value is not None})
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), default=str)
