import base64
import threading
import time
from dataclasses import dataclass, field

import openai as openai_sdk

from config import config
from modules import log
from modules.ai.providers.base import AIClientError, AIServerError

logger = log.Logger()

DEFAULT_MODEL = "gpt-4o"

EXCLUDED_KEYWORDS = ("embedding", "tts", "whisper", "dall-e", "moderation", "babbage", "davinci")


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

        with self._lock:
            session = self._get_or_create_session(session_key)

        user_content = self._build_user_content(text, image)

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

            try:
                response = self.client.responses.create(**kwargs)
            except openai_sdk.APITimeoutError as e:
                logger.log_error(f"OpenAI API timeout: {e}")
                session.messages.pop()
                raise TimeoutError("OpenAI API timeout") from e
            except openai_sdk.APIStatusError as e:
                logger.log_error(f"OpenAI API status error {e.status_code}: {e}")
                session.messages.pop()
                if e.status_code < 500:
                    raise AIClientError(str(e)) from e
                raise AIServerError(str(e)) from e
            except Exception as e:
                logger.log_error(f"OpenAI API call failed: {e}")
                session.messages.pop()
                raise AIServerError(str(e)) from e

            result = response.output_text
            session.messages.append({"role": "assistant", "content": result})
            session.last_active = time.time()
            self._trim_history(session_key)

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
            return sorted(m.id for m in self.client.models.list() if not any(kw in m.id for kw in EXCLUDED_KEYWORDS))
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
