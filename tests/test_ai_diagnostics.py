import json

from modules.ai.diagnostics import build_diagnostic_event, sanitize_traceback


def test_sanitize_traceback_redacts_sensitive_values_and_preserves_stack():
    question = "민감한 질문"
    api_key = "configured-private-key"

    try:
        try:
            raise ValueError(f"failed for {question} with {api_key} and sk-pattern-secret")
        except ValueError as cause:
            raise RuntimeError("Bearer private-token") from cause
    except RuntimeError as error:
        sanitized = sanitize_traceback(error, (question, api_key))

    assert "Traceback (most recent call last)" in sanitized
    assert "ValueError" in sanitized
    assert "RuntimeError" in sanitized
    assert question not in sanitized
    assert api_key not in sanitized
    assert "sk-pattern-secret" not in sanitized
    assert "private-token" not in sanitized
    assert "[REDACTED]" in sanitized


def test_diagnostic_event_keeps_sanitized_traceback_on_one_line():
    try:
        raise RuntimeError("failure")
    except RuntimeError as error:
        sanitized = sanitize_traceback(error)

    serialized = build_diagnostic_event("test.failure", "실패", traceback=sanitized)

    assert "\n" not in serialized
    assert "\\n" in serialized
    assert json.loads(serialized)["traceback"] == sanitized
