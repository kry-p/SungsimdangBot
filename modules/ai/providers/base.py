from typing import Protocol, runtime_checkable


class AIError(Exception):
    """Base exception for AI provider errors."""


class AIClientError(AIError):
    """Client-side error (bad request, quota exceeded, etc.)."""


class AIServerError(AIError):
    """Server-side error (temporary provider issue)."""


@runtime_checkable
class AIProvider(Protocol):
    model: str
    search_enabled: bool

    def ask(self, session_key: tuple, system_prompt: str, text: str, image: bytes | None = None) -> str: ...
    def clear_session(self, session_key: tuple) -> None: ...
    def reset_sessions(self) -> None: ...
    def list_models(self) -> list[str]: ...
    def set_model(self, model_name: str) -> None: ...
    def set_search(self, enabled: bool) -> None: ...
    def supports_search(self) -> bool: ...
    def cleanup_expired(self, timeout: float) -> None: ...
