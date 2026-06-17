import concurrent.futures
import threading
import time
from unittest.mock import MagicMock, patch

import pytest
from google.genai.errors import ClientError, ServerError

from modules.ai.providers.base import AIClientError, AIServerError
from modules.ai.providers.gemini import GeminiProvider


def make_provider(**kwargs):
    with patch.object(GeminiProvider, "__init__", lambda self, **kw: None):
        p = GeminiProvider()
        p._lock = threading.RLock()
        p._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        p.client = MagicMock()
        p.model = "gemini-2.5-flash"
        p.search_enabled = False
        p.sessions = {}
        for k, v in kwargs.items():
            setattr(p, k, v)
    return p


class TestAsk:
    def test_normal_response(self):
        p = make_provider()
        mock_chat = MagicMock()
        mock_chat.send_message.return_value.text = "답변"
        mock_chat.send_message.return_value.candidates = []
        mock_chat.get_history.return_value = []
        p.client.chats.create.return_value = mock_chat

        result = p.ask((1, 1), "system", "질문")
        assert result == "답변"

    def test_no_client_raises(self):
        p = make_provider(client=None)
        with pytest.raises(AIClientError):
            p.ask((1, 1), "system", "질문")

    def test_timeout_raises(self):
        p = make_provider()
        mock_chat = MagicMock()
        mock_chat.send_message.side_effect = lambda q: time.sleep(10)
        p.client.chats.create.return_value = mock_chat

        with patch("modules.ai.providers.gemini.config") as mock_config:
            mock_config.AI_API_TIMEOUT = 0.1
            mock_config.AI_SESSION_TIMEOUT = 3600
            mock_config.AI_MAX_HISTORY = 20
            with pytest.raises(TimeoutError):
                p.ask((1, 1), "system", "질문")

    def test_client_error_raises(self):
        p = make_provider()
        mock_chat = MagicMock()
        mock_chat.send_message.side_effect = ClientError(429, {"error": "quota"})
        p.client.chats.create.return_value = mock_chat

        with pytest.raises(AIClientError):
            p.ask((1, 1), "system", "질문")

    def test_server_error_raises(self):
        p = make_provider()
        mock_chat = MagicMock()
        mock_chat.send_message.side_effect = ServerError(500, {"error": "internal"})
        p.client.chats.create.return_value = mock_chat

        with pytest.raises(AIServerError):
            p.ask((1, 1), "system", "질문")

    def test_with_image(self):
        p = make_provider()
        mock_chat = MagicMock()
        mock_chat.send_message.return_value.text = "이미지 설명"
        mock_chat.send_message.return_value.candidates = []
        mock_chat.get_history.return_value = []
        p.client.chats.create.return_value = mock_chat

        result = p.ask((1, 1), "system", "이게 뭐야", image=b"fake_image")
        assert result == "이미지 설명"
        sent = mock_chat.send_message.call_args[0][0]
        assert isinstance(sent, list)
        assert len(sent) == 2

    def test_search_grounding_config_passed(self):
        p = make_provider(search_enabled=True)
        mock_chat = MagicMock()
        mock_chat.send_message.return_value.text = "답변"
        mock_chat.send_message.return_value.candidates = []
        mock_chat.get_history.return_value = []
        p.client.chats.create.return_value = mock_chat

        p.ask((1, 1), "system", "질문")
        config_arg = p.client.chats.create.call_args.kwargs["config"]
        assert config_arg.tools is not None

    def test_grounding_sources_appended(self):
        p = make_provider(search_enabled=True)
        mock_chat = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "답변"
        mock_chunk = MagicMock()
        mock_chunk.web.title = "참고"
        mock_chunk.web.uri = "https://example.com"
        mock_response.candidates = [MagicMock()]
        mock_response.candidates[0].grounding_metadata.grounding_chunks = [mock_chunk]
        mock_chat.send_message.return_value = mock_response
        mock_chat.get_history.return_value = []
        p.client.chats.create.return_value = mock_chat

        result = p.ask((1, 1), "system", "질문")
        assert "참고한 자료" in result
        assert "[참고](https://example.com)" in result

    def test_separate_sessions_per_key(self):
        p = make_provider()
        chat_a, chat_b = MagicMock(), MagicMock()
        for mc in (chat_a, chat_b):
            mc.send_message.return_value.text = "ok"
            mc.send_message.return_value.candidates = []
            mc.get_history.return_value = []
        p.client.chats.create.side_effect = [chat_a, chat_b]

        p.ask((1, 1), "sys", "q1")
        p.ask((1, 2), "sys", "q2")
        assert (1, 1) in p.sessions
        assert (1, 2) in p.sessions
        assert p.client.chats.create.call_count == 2

    def test_session_reused(self):
        p = make_provider()
        mock_chat = MagicMock()
        mock_chat.send_message.return_value.text = "ok"
        mock_chat.send_message.return_value.candidates = []
        mock_chat.get_history.return_value = []
        p.client.chats.create.return_value = mock_chat

        p.ask((1, 1), "sys", "q1")
        p.ask((1, 1), "sys", "q2")
        assert p.client.chats.create.call_count == 1


class TestSessionManagement:
    def test_clear_session(self):
        p = make_provider()
        p.sessions[(1, 1)] = MagicMock()
        p.clear_session((1, 1))
        assert (1, 1) not in p.sessions

    def test_clear_nonexistent_session(self):
        p = make_provider()
        p.clear_session((999, 1))  # should not raise

    def test_reset_sessions(self):
        p = make_provider()
        p.sessions = {(1, 1): MagicMock(), (2, 2): MagicMock()}
        p.reset_sessions()
        assert p.sessions == {}

    @patch("modules.ai.providers.gemini.config")
    def test_expire_after_timeout(self, mock_config):
        mock_config.AI_SESSION_TIMEOUT = 3600
        from modules.ai.providers.gemini import GeminiSession

        p = make_provider()
        p.sessions[(1, 1)] = GeminiSession(chat=MagicMock(), last_active=time.time() - 3601)
        assert p._expire_session_if_needed((1, 1)) is True
        assert (1, 1) not in p.sessions

    @patch("modules.ai.providers.gemini.config")
    def test_no_expire_within_timeout(self, mock_config):
        mock_config.AI_SESSION_TIMEOUT = 3600
        from modules.ai.providers.gemini import GeminiSession

        p = make_provider()
        p.sessions[(1, 1)] = GeminiSession(chat=MagicMock(), last_active=time.time())
        assert p._expire_session_if_needed((1, 1)) is False

    @patch("modules.ai.providers.gemini.config")
    def test_cleanup_expired(self, mock_config):
        mock_config.AI_SESSION_TIMEOUT = 3600
        from modules.ai.providers.gemini import GeminiSession

        p = make_provider()
        p.sessions = {
            (1, 1): GeminiSession(chat=MagicMock(), last_active=time.time() - 7200),
            (2, 2): GeminiSession(chat=MagicMock(), last_active=time.time()),
        }
        p.cleanup_expired(3600)
        assert (1, 1) not in p.sessions
        assert (2, 2) in p.sessions

    @patch("modules.ai.providers.gemini.config")
    def test_trim_history(self, mock_config):
        mock_config.AI_MAX_HISTORY = 2
        mock_config.AI_SESSION_TIMEOUT = 3600
        from modules.ai.providers.gemini import GeminiSession

        p = make_provider()
        mock_chat = MagicMock()
        mock_chat.get_history.return_value = ["a", "b", "c", "d", "e", "f"]
        p.sessions[(1, 1)] = GeminiSession(chat=mock_chat)
        new_chat = MagicMock()
        p.client.chats.create.return_value = new_chat

        p._trim_history((1, 1), "system")
        call_kwargs = p.client.chats.create.call_args
        assert call_kwargs.kwargs["history"] == ["c", "d", "e", "f"]


class TestModelAndSearch:
    def test_set_model_clears_sessions(self):
        p = make_provider()
        p.sessions = {(1, 1): MagicMock()}
        p.set_model("gemini-2.5-pro")
        assert p.model == "gemini-2.5-pro"
        assert p.sessions == {}

    def test_set_search_clears_sessions(self):
        p = make_provider()
        p.sessions = {(1, 1): MagicMock()}
        p.set_search(True)
        assert p.search_enabled is True
        assert p.sessions == {}

    def test_supports_search(self):
        p = make_provider()
        assert p.supports_search() is True

    def test_list_models_filters_correctly(self):
        p = make_provider()
        m1 = MagicMock()
        m1.name = "models/gemini-2.5-flash"
        m1.supported_actions = ["generateContent"]
        m2 = MagicMock()
        m2.name = "models/gemini-embedding-001"
        m2.supported_actions = ["embedContent"]
        m3 = MagicMock()
        m3.name = "models/gemini-2.5-flash-tts"
        m3.supported_actions = ["generateContent"]
        p.client.models.list.return_value = [m1, m2, m3]
        assert p.list_models() == ["gemini-2.5-flash"]

    def test_list_models_no_client(self):
        p = make_provider(client=None)
        assert p.list_models() == []

    def test_list_models_api_error(self):
        p = make_provider()
        p.client.models.list.side_effect = Exception("error")
        assert p.list_models() == []
