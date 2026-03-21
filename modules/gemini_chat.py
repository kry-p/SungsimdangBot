import re
import threading
import time
from dataclasses import dataclass, field

from google import genai
from google.genai import types

from config import config
from modules import log
from modules.database import AllowedChat
from modules.settings import Settings
from resources import strings

logger = log.Logger()

DEFAULT_MODEL = "gemini-2.5-flash"

SETTINGS_MODULE_PATH = "modules.gemini_chat"
EXCLUDED_KEYWORDS = ("embedding", "tts", "audio", "image", "robotics", "computer-use", "deep-research", "aqa")


@dataclass
class ManagedSession:
    chat: object
    last_active: float = field(default_factory=time.time)


class GeminiChat:
    def __init__(self):
        self._lock = threading.RLock()
        self.client = None
        if config.GEMINI_API_KEY:
            self.client = genai.Client(api_key=config.GEMINI_API_KEY)
        self.model = Settings().get(SETTINGS_MODULE_PATH, "model", DEFAULT_MODEL)
        self.sessions = {}
        self.request_counts = {}

    # --- 핵심 기능 ---

    def ask(self, chat_id, question, language_code):
        with self._lock:
            if not self.client:
                return [strings.ask_error_msg]

            if not self.is_chat_allowed(chat_id):
                return [strings.ask_not_allowed_msg]

            if not self.check_rate_limit(chat_id):
                return [strings.ask_rate_limit_msg]

            self._expire_session_if_needed(chat_id)
            managed = self._get_or_create_session(chat_id, language_code)

            try:
                response = managed.chat.send_message(question)
                result = response.text
            except Exception:
                logger.log_error("Gemini API call failed.")
                return [strings.ask_error_msg]

            self._trim_history(chat_id, language_code)
            managed.last_active = time.time()

            return self.split_response(result)

    def clear_session(self, chat_id):
        with self._lock:
            self.sessions.pop(chat_id, None)

    # --- 세션 관리 ---

    def _get_or_create_session(self, chat_id, language_code):
        if chat_id not in self.sessions:
            chat = self.client.chats.create(
                model=self.model,
                config=types.GenerateContentConfig(
                    system_instruction=self._build_system_prompt(language_code),
                ),
            )
            self.sessions[chat_id] = ManagedSession(chat=chat)
        return self.sessions[chat_id]

    def _expire_session_if_needed(self, chat_id):
        managed = self.sessions.get(chat_id)
        if managed and time.time() - managed.last_active > config.GEMINI_SESSION_TIMEOUT:
            del self.sessions[chat_id]
            return True
        return False

    def _trim_history(self, chat_id, language_code):
        managed = self.sessions.get(chat_id)
        if not managed:
            return
        history = managed.chat.get_history()
        max_entries = config.GEMINI_MAX_HISTORY * 2
        if len(history) > max_entries:
            trimmed = history[-max_entries:]
            managed.chat = self.client.chats.create(
                model=self.model,
                config=types.GenerateContentConfig(
                    system_instruction=self._build_system_prompt(language_code),
                ),
                history=trimmed,
            )

    _LANGUAGE_CODE_PATTERN = re.compile(r"^[a-z]{2}(-[A-Z]{2})?$")

    @staticmethod
    def _build_system_prompt(language_code):
        if language_code and GeminiChat._LANGUAGE_CODE_PATTERN.match(language_code):
            return (
                f"Respond in the language with code '{language_code}'."
                " If unsure, respond in the same language as the user's question."
            )
        return "Respond in the same language as the user's question."

    # --- Rate limit ---

    def check_rate_limit(self, chat_id):
        now = time.time()
        timestamps = self.request_counts.get(chat_id, [])
        timestamps = [t for t in timestamps if now - t < 60]
        if not timestamps:
            self.request_counts.pop(chat_id, None)
        if len(timestamps) >= config.GEMINI_RATE_LIMIT:
            self.request_counts[chat_id] = timestamps
            return False
        timestamps.append(now)
        self.request_counts[chat_id] = timestamps
        return True

    # --- 모델 관리 ---

    def list_models(self):
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

    def set_model(self, model_name):
        with self._lock:
            self.model = model_name
            self.sessions.clear()
            Settings().set(SETTINGS_MODULE_PATH, "model", model_name)

    # --- 허용 목록 ---

    def is_chat_allowed(self, chat_id):
        return AllowedChat.select().where(AllowedChat.chat_id == chat_id).exists()

    def allow_chat(self, chat_id, name=""):
        with self._lock:
            AllowedChat.replace(chat_id=chat_id, name=name).execute()

    def deny_chat(self, chat_id):
        with self._lock:
            AllowedChat.delete().where(AllowedChat.chat_id == chat_id).execute()

    def get_chat_name(self, chat_id):
        row = AllowedChat.get_or_none(AllowedChat.chat_id == chat_id)
        return row.name if row else ""

    def list_allowed_chats(self):
        return [{"id": row.chat_id, "name": row.name} for row in AllowedChat.select().order_by(AllowedChat.chat_id)]

    # --- 응답 분할 ---

    @staticmethod
    def split_response(text, max_len=4096):
        if len(text) <= max_len:
            return [text]
        chunks = []
        while text:
            if len(text) <= max_len:
                chunks.append(text)
                break
            split_at = text.rfind("\n", 0, max_len)
            if split_at == -1:
                split_at = max_len
            chunks.append(text[:split_at])
            text = text[split_at:].lstrip("\n")
        return chunks
