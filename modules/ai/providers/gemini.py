import concurrent.futures
import threading
import time
from dataclasses import dataclass, field

from google import genai
from google.genai import types
from google.genai.errors import ClientError, ServerError

from config import config
from modules import log
from modules.ai.providers.base import AIClientError, AIServerError
from resources import strings

logger = log.Logger()

DEFAULT_MODEL = "gemini-2.5-flash"
EXCLUDED_KEYWORDS = ("embedding", "tts", "audio", "image", "robotics", "computer-use", "deep-research", "aqa")


@dataclass
class GeminiSession:
    chat: object
    last_active: float = field(default_factory=time.time)


class GeminiProvider:
    def __init__(self, model: str = DEFAULT_MODEL, search_enabled: bool = False):
        self._lock = threading.RLock()
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self.client = None
        if config.GEMINI_API_KEY:
            self.client = genai.Client(api_key=config.GEMINI_API_KEY)
        self.model = model
        self.search_enabled = search_enabled
        self.sessions: dict[tuple, GeminiSession] = {}

    def ask(self, session_key: tuple, system_prompt: str, text: str, image: bytes | None = None) -> str:
        if not self.client:
            raise AIClientError("Gemini API key not configured")

        with self._lock:
            self._expire_session_if_needed(session_key)
            managed = self._get_or_create_session(session_key, system_prompt)

        prompt = self._build_prompt(text, image)

        try:
            future = self._executor.submit(managed.chat.send_message, prompt)
            response = future.result(timeout=config.AI_API_TIMEOUT)
            result = response.text
        except concurrent.futures.TimeoutError:
            logger.log_error("Gemini API call timed out.")
            raise TimeoutError("Gemini API timeout") from None
        except ClientError as e:
            logger.log_error(f"Gemini API client error: {e}")
            raise AIClientError(str(e)) from e
        except ServerError as e:
            logger.log_error(f"Gemini API server error: {e}")
            raise AIServerError(str(e)) from e
        except Exception as e:
            logger.log_error(f"Gemini API call failed: {e}")
            raise AIServerError(str(e)) from e

        with self._lock:
            result = self._append_grounding_sources(response, result)
            self._trim_history(session_key, system_prompt)
            managed.last_active = time.time()

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
            models = []
            for m in self.client.models.list():
                name = m.name.removeprefix("models/")
                actions = getattr(m, "supported_actions", []) or []
                if "gemini" not in name:
                    continue
                if "generateContent" not in actions:
                    continue
                if any(kw in name for kw in EXCLUDED_KEYWORDS):
                    continue
                models.append(name)
            return sorted(models)
        except Exception:
            logger.log_error("Failed to list Gemini models.")
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

    def _get_or_create_session(self, session_key: tuple, system_prompt: str) -> GeminiSession:
        if session_key not in self.sessions:
            chat = self.client.chats.create(
                model=self.model,
                config=self._build_config(system_prompt),
            )
            self.sessions[session_key] = GeminiSession(chat=chat)
        return self.sessions[session_key]

    def _expire_session_if_needed(self, session_key: tuple) -> bool:
        managed = self.sessions.get(session_key)
        if managed and time.time() - managed.last_active > config.AI_SESSION_TIMEOUT:
            del self.sessions[session_key]
            return True
        return False

    def _build_config(self, system_prompt: str) -> types.GenerateContentConfig:
        config_kwargs: dict = {"system_instruction": system_prompt}
        if self.search_enabled:
            config_kwargs["tools"] = [types.Tool(google_search=types.GoogleSearch())]
        return types.GenerateContentConfig(**config_kwargs)

    def _trim_history(self, session_key: tuple, system_prompt: str) -> None:
        managed = self.sessions.get(session_key)
        if not managed:
            return
        history = managed.chat.get_history()
        max_entries = config.AI_MAX_HISTORY * 2
        if len(history) > max_entries:
            trimmed = history[-max_entries:]
            managed.chat = self.client.chats.create(
                model=self.model,
                config=self._build_config(system_prompt),
                history=trimmed,
            )

    @staticmethod
    def _build_prompt(text: str, image: bytes | None):
        if image:
            return [
                types.Part.from_bytes(data=image, mime_type="image/jpeg"),
                types.Part.from_text(text=text),
            ]
        return text

    @staticmethod
    def _append_grounding_sources(response, text: str) -> str:
        metadata = getattr(response.candidates[0], "grounding_metadata", None) if response.candidates else None
        if not metadata:
            return text
        chunks = getattr(metadata, "grounding_chunks", None)
        if not chunks:
            return text
        sources = strings.grounding_sources_label
        for chunk in chunks:
            web = getattr(chunk, "web", None)
            if web:
                sources += f"\n- [{web.title}]({web.uri})"
        return text + sources
