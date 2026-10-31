import base64
import re
import threading
import time
import uuid
from dataclasses import dataclass, field

import openai as openai_sdk

from config import config
from modules import log
from modules.ai.diagnostics import build_diagnostic_event, sanitize_exception_message, sanitize_traceback
from modules.ai.providers.base import AIClientError, AIServerError
from resources import strings

logger = log.Logger()

DEFAULT_MODEL = "gpt-4o"

# gpt-*, o1/o3/o4-* 계열 텍스트 생성 모델만 허용
_CHAT_MODEL_RE = re.compile(r"^(gpt-|o\d|chatgpt-)")

# 텍스트 생성과 무관한 특수 기능 모델 제외 (화이트리스트 통과 후 추가 필터)
EXCLUDED_KEYWORDS = ("audio", "realtime", "image", "preview", "instruct")

# -0613, -1106, -2024-05-13 같은 날짜 버전 suffix 제외
_DATED_VERSION_RE = re.compile(r"-\d{4}")


def _safe_scalar(value):
    return value if isinstance(value, (str, int, float, bool)) else None


def _safe_attribute(obj, name):
    if isinstance(obj, dict):
        return obj.get(name)
    try:
        return getattr(obj, name, None)
    except Exception:
        return None


def _response_diagnostics(response) -> dict:
    output = _safe_attribute(response, "output")
    output_items = output if isinstance(output, (list, tuple)) else []
    output_item_types = [
        item_type for item in output_items if (item_type := _safe_scalar(_safe_attribute(item, "type"))) is not None
    ]
    response_error = _safe_attribute(response, "error")
    incomplete_details = _safe_attribute(response, "incomplete_details")
    return {
        "response_id": _safe_scalar(_safe_attribute(response, "id")),
        "request_id": _safe_scalar(_safe_attribute(response, "_request_id")),
        "response_status": _safe_scalar(_safe_attribute(response, "status")),
        "output_item_types": output_item_types,
        "output_item_count": len(output_items),
        "web_search_call_count": output_item_types.count("web_search_call"),
        "response_error_type": _safe_scalar(_safe_attribute(response_error, "type")),
        "response_error_code": _safe_scalar(_safe_attribute(response_error, "code")),
        "incomplete_reason": _safe_scalar(_safe_attribute(incomplete_details, "reason")),
    }


def _api_error_diagnostics(error) -> dict:
    body = _safe_attribute(error, "body")
    error_body = body.get("error", body) if isinstance(body, dict) else {}
    if not isinstance(error_body, dict):
        error_body = {}
    cause = error.__cause__
    return {
        "status_code": _safe_scalar(_safe_attribute(error, "status_code")),
        "request_id": _safe_scalar(_safe_attribute(error, "request_id")),
        "error_type": _safe_scalar(error_body.get("type")),
        "error_code": _safe_scalar(error_body.get("code")),
        "cause_type": type(cause).__name__ if cause is not None else None,
    }


@dataclass
class OpenAISession:
    messages: list = field(default_factory=list)
    last_active: float = field(default_factory=time.time)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)


class OpenAIProvider:
    def __init__(self, model: str = DEFAULT_MODEL, search_enabled: bool = False):
        self._lock = threading.RLock()
        self.client = None
        if config.OPENAI_API_KEY:
            self.client = openai_sdk.OpenAI(
                api_key=config.OPENAI_API_KEY,
                base_url=config.OPENAI_BASE_URL,
            )
        self.model = model
        self.search_enabled = search_enabled
        self.sessions: dict[tuple, OpenAISession] = {}

    def ask(self, session_key: tuple, system_prompt: str, text: str, image: bytes | None = None) -> str:
        if not self.client:
            raise AIClientError("OpenAI API key not configured")

        operation_id = uuid.uuid4().hex[:12]
        request_started_at = time.perf_counter()

        with self._lock:
            session = self._get_or_create_session(session_key)

        user_content = self._build_user_content(text, image)
        image_url = user_content[0]["image_url"] if isinstance(user_content, list) else None
        sensitive_values = (system_prompt, text, image_url, config.OPENAI_API_KEY)

        with session._lock:
            session.messages.append({"role": "user", "content": user_content})
            messages_snapshot = list(session.messages)

            kwargs = {
                "model": self.model,
                "instructions": system_prompt,
                "input": messages_snapshot,
            }
            if self.search_enabled:
                kwargs["tools"] = [{"type": "web_search_preview"}]

            logger.log_info(
                build_diagnostic_event(
                    "ai.openai.request_started",
                    strings.ask_openai_request_started_log_msg,
                    operation_id=operation_id,
                    model=self.model,
                    search_enabled=self.search_enabled,
                    has_image=image is not None,
                    input_kind="text_image" if image is not None else "text",
                    history_entry_count=len(messages_snapshot),
                )
            )
            api_started_at = time.perf_counter()
            try:
                response = self.client.responses.create(**kwargs)
            except openai_sdk.APITimeoutError as e:
                logger.log_error(
                    build_diagnostic_event(
                        "ai.openai.request_failed",
                        strings.ask_openai_request_failed_log_error_msg,
                        operation_id=operation_id,
                        stage="api_call",
                        model=self.model,
                        error_category="timeout",
                        elapsed_ms=round((time.perf_counter() - request_started_at) * 1000),
                        exception_type=type(e).__name__,
                        exception_message=sanitize_exception_message(e, sensitive_values),
                        traceback=sanitize_traceback(e, sensitive_values),
                        **_api_error_diagnostics(e),
                    )
                )
                session.messages.pop()
                raise TimeoutError("OpenAI API timeout") from e
            except openai_sdk.APIConnectionError as e:
                logger.log_error(
                    build_diagnostic_event(
                        "ai.openai.request_failed",
                        strings.ask_openai_request_failed_log_error_msg,
                        operation_id=operation_id,
                        stage="api_call",
                        model=self.model,
                        error_category="connection",
                        elapsed_ms=round((time.perf_counter() - request_started_at) * 1000),
                        exception_type=type(e).__name__,
                        exception_message=sanitize_exception_message(e, sensitive_values),
                        traceback=sanitize_traceback(e, sensitive_values),
                        **_api_error_diagnostics(e),
                    )
                )
                session.messages.pop()
                raise AIServerError(str(e)) from e
            except openai_sdk.APIStatusError as e:
                error_category = "rate_limit" if e.status_code == 429 else "client_error"
                if e.status_code >= 500:
                    error_category = "server_error"
                logger.log_error(
                    build_diagnostic_event(
                        "ai.openai.request_failed",
                        strings.ask_openai_request_failed_log_error_msg,
                        operation_id=operation_id,
                        stage="api_call",
                        model=self.model,
                        error_category=error_category,
                        elapsed_ms=round((time.perf_counter() - request_started_at) * 1000),
                        exception_type=type(e).__name__,
                        exception_message=sanitize_exception_message(e, sensitive_values),
                        traceback=sanitize_traceback(e, sensitive_values),
                        **_api_error_diagnostics(e),
                    )
                )
                session.messages.pop()
                if e.status_code < 500:
                    raise AIClientError(str(e)) from e
                raise AIServerError(str(e)) from e
            except Exception as e:
                logger.log_error(
                    build_diagnostic_event(
                        "ai.openai.request_failed",
                        strings.ask_openai_request_failed_log_error_msg,
                        operation_id=operation_id,
                        stage="api_call",
                        model=self.model,
                        error_category="unexpected",
                        elapsed_ms=round((time.perf_counter() - request_started_at) * 1000),
                        exception_type=type(e).__name__,
                        exception_message=sanitize_exception_message(e, sensitive_values),
                        traceback=sanitize_traceback(e, sensitive_values),
                        **_api_error_diagnostics(e),
                    )
                )
                session.messages.pop()
                raise AIServerError(str(e)) from e

            api_elapsed_ms = round((time.perf_counter() - api_started_at) * 1000)
            response_diagnostics = _response_diagnostics(response)
            try:
                result = response.output_text
            except Exception as e:
                logger.log_error(
                    build_diagnostic_event(
                        "ai.openai.postprocess_failed",
                        strings.ask_openai_postprocess_failed_log_error_msg,
                        operation_id=operation_id,
                        stage="response_extract",
                        model=self.model,
                        elapsed_ms=round((time.perf_counter() - request_started_at) * 1000),
                        exception_type=type(e).__name__,
                        exception_message=sanitize_exception_message(e, sensitive_values),
                        traceback=sanitize_traceback(e, sensitive_values),
                        **response_diagnostics,
                    )
                )
                raise AIServerError(str(e)) from e
            if not result:
                logger.log_error(
                    build_diagnostic_event(
                        "ai.openai.response_invalid",
                        strings.ask_openai_response_invalid_log_error_msg,
                        operation_id=operation_id,
                        stage="response_extract",
                        model=self.model,
                        elapsed_ms=round((time.perf_counter() - request_started_at) * 1000),
                        output_text_present=False,
                        **response_diagnostics,
                    )
                )
                session.messages.pop()
                raise AIServerError("Empty response from OpenAI")
            session.messages.append({"role": "assistant", "content": result})
            session.last_active = time.time()
            try:
                self._trim_history(session_key)
            except Exception as e:
                logger.log_error(
                    build_diagnostic_event(
                        "ai.openai.postprocess_failed",
                        strings.ask_openai_postprocess_failed_log_error_msg,
                        operation_id=operation_id,
                        stage="history_trim",
                        model=self.model,
                        elapsed_ms=round((time.perf_counter() - request_started_at) * 1000),
                        output_char_count=len(result) if isinstance(result, str) else None,
                        exception_type=type(e).__name__,
                        exception_message=sanitize_exception_message(e, sensitive_values),
                        traceback=sanitize_traceback(e, sensitive_values),
                        **response_diagnostics,
                    )
                )
                raise AIServerError(str(e)) from e

            logger.log_info(
                build_diagnostic_event(
                    "ai.openai.request_succeeded",
                    strings.ask_openai_request_succeeded_log_msg,
                    operation_id=operation_id,
                    model=self.model,
                    elapsed_ms=round((time.perf_counter() - request_started_at) * 1000),
                    api_elapsed_ms=api_elapsed_ms,
                    output_char_count=len(result) if isinstance(result, str) else None,
                    history_entry_count=len(session.messages),
                    **response_diagnostics,
                )
            )

        return result

    def clear_session(self, session_key: tuple) -> None:
        with self._lock:
            self.sessions.pop(session_key, None)

    def reset_sessions(self) -> None:
        with self._lock:
            self.sessions.clear()

    def list_models(self) -> list[str]:
        if not self.client:
            return []
        try:
            return sorted(
                m.id
                for m in self.client.models.list()
                if _CHAT_MODEL_RE.match(m.id)
                and not any(kw in m.id for kw in EXCLUDED_KEYWORDS)
                and not _DATED_VERSION_RE.search(m.id)
            )
        except Exception:
            logger.log_error("Failed to list OpenAI models.")
            return []

    def set_model(self, model_name: str) -> None:
        with self._lock:
            self.model = model_name
            self.sessions.clear()

    def set_search(self, enabled: bool) -> None:
        with self._lock:
            self.search_enabled = enabled
            self.sessions.clear()

    def supports_search(self) -> bool:
        return True

    def cleanup_expired(self, timeout: float) -> None:
        with self._lock:
            now = time.time()
            expired = [k for k, v in self.sessions.items() if now - v.last_active > timeout]
            for k in expired:
                del self.sessions[k]

    def _get_or_create_session(self, session_key: tuple) -> OpenAISession:
        if session_key not in self.sessions:
            self.sessions[session_key] = OpenAISession()
        return self.sessions[session_key]

    def _trim_history(self, session_key: tuple) -> None:
        session = self.sessions.get(session_key)
        if not session:
            return
        max_entries = config.AI_MAX_HISTORY * 2
        if len(session.messages) > max_entries:
            session.messages = session.messages[-max_entries:]

    @staticmethod
    def _build_user_content(text: str, image: bytes | None):
        if image:
            b64 = base64.b64encode(image).decode()
            return [
                {"type": "input_image", "image_url": f"data:image/jpeg;base64,{b64}"},
                {"type": "input_text", "text": text},
            ]
        return text
