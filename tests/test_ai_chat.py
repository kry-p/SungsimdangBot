import threading
import time
from unittest.mock import MagicMock, patch

from modules.ai.chat import AIChatManager
from modules.database import AllowedChat
from resources import strings


def make_manager(provider_mock=None, allowlist=None, **overrides):
    allowlist = allowlist or {}
    for chat_id, name in allowlist.items():
        AllowedChat.replace(chat_id=chat_id, name=name).execute()

    with patch.object(AIChatManager, "__init__", lambda self: None):
        m = AIChatManager()
        m._lock = threading.RLock()
        m.provider = provider_mock or MagicMock()
        m.request_counts = {}
        m.custom_prompt = ""
        for k, v in overrides.items():
            setattr(m, k, v)
    return m


def make_provider_mock(response="답변"):
    mock = MagicMock()
    mock.ask.return_value = response
    mock.model = "gemini-2.5-flash"
    mock.search_enabled = False
    mock.supports_search.return_value = True
    return mock


class TestAsk:
    def test_not_allowed(self):
        m = make_manager(allowlist={})
        result = m.ask(1, 1, "질문", "ko")
        assert result == [strings.ask_not_allowed_msg]

    def test_rate_limited(self):
        m = make_manager(allowlist={1: "test"})
        m.request_counts = {1: [time.time() for _ in range(5)]}
        with patch("modules.ai.chat.config") as mc:
            mc.AI_RATE_LIMIT = 5
            result = m.ask(1, 1, "질문", "ko")
        assert result == [strings.ask_rate_limit_msg]

    def test_success(self):
        provider = make_provider_mock("답변")
        m = make_manager(provider_mock=provider, allowlist={1: "test"})
        with patch("modules.ai.chat.config") as mc:
            mc.AI_RATE_LIMIT = 5
            result = m.ask(1, 1, "질문", "ko")
        assert result == ["답변"]
        provider.ask.assert_called_once()

    def test_timeout_error(self):
        provider = make_provider_mock()
        provider.ask.side_effect = TimeoutError
        m = make_manager(provider_mock=provider, allowlist={1: "test"})
        with patch("modules.ai.chat.config") as mc:
            mc.AI_RATE_LIMIT = 5
            result = m.ask(1, 1, "질문", "ko")
        assert result == [strings.ask_timeout_msg]

    def test_client_error(self):
        from modules.ai.providers.base import AIClientError

        provider = make_provider_mock()
        provider.ask.side_effect = AIClientError
        m = make_manager(provider_mock=provider, allowlist={1: "test"})
        with patch("modules.ai.chat.config") as mc:
            mc.AI_RATE_LIMIT = 5
            result = m.ask(1, 1, "질문", "ko")
        assert result == [strings.ask_client_error_msg]

    def test_server_error(self):
        from modules.ai.providers.base import AIServerError

        provider = make_provider_mock()
        provider.ask.side_effect = AIServerError
        m = make_manager(provider_mock=provider, allowlist={1: "test"})
        with patch("modules.ai.chat.config") as mc:
            mc.AI_RATE_LIMIT = 5
            result = m.ask(1, 1, "질문", "ko")
        assert result == [strings.ask_error_msg]

    def test_context_included_in_prompt(self):
        provider = make_provider_mock()
        m = make_manager(provider_mock=provider, allowlist={1: "test"})
        with patch("modules.ai.chat.config") as mc:
            mc.AI_RATE_LIMIT = 5
            m.ask(1, 1, "요약해줘", "ko", context="원본 메시지")
        _, _, text, _ = provider.ask.call_args[0]
        assert "원본 메시지" in text
        assert "요약해줘" in text

    def test_system_prompt_includes_language(self):
        provider = make_provider_mock()
        m = make_manager(provider_mock=provider, allowlist={1: "test"})
        with patch("modules.ai.chat.config") as mc:
            mc.AI_RATE_LIMIT = 5
            m.ask(1, 1, "질문", "ko")
        _, system_prompt, _, _ = provider.ask.call_args[0]
        assert "'ko'" in system_prompt

    def test_custom_prompt_in_system_prompt(self):
        provider = make_provider_mock()
        m = make_manager(provider_mock=provider, allowlist={1: "test"}, custom_prompt="항상 짧게 답해.")
        with patch("modules.ai.chat.config") as mc:
            mc.AI_RATE_LIMIT = 5
            m.ask(1, 1, "질문", "ko")
        _, system_prompt, _, _ = provider.ask.call_args[0]
        assert "항상 짧게 답해." in system_prompt

    def test_long_response_split(self):
        long_text = "a" * 4000 + "\n" + "b" * 200
        provider = make_provider_mock(long_text)
        m = make_manager(provider_mock=provider, allowlist={1: "test"})
        with patch("modules.ai.chat.config") as mc:
            mc.AI_RATE_LIMIT = 5
            result = m.ask(1, 1, "질문", "ko")
        assert len(result) == 2


class TestRateLimit:
    def test_within_limit(self):
        m = make_manager()
        with patch("modules.ai.chat.config") as mc:
            mc.AI_RATE_LIMIT = 5
            assert m.check_rate_limit(1, 1) is True

    def test_at_chat_limit(self):
        m = make_manager()
        m.request_counts = {1: [time.time() for _ in range(5)]}
        with patch("modules.ai.chat.config") as mc:
            mc.AI_RATE_LIMIT = 5
            assert m.check_rate_limit(1, 1) is False

    def test_at_user_limit(self):
        m = make_manager()
        m.request_counts = {"user:1": [time.time() for _ in range(5)]}
        with patch("modules.ai.chat.config") as mc:
            mc.AI_RATE_LIMIT = 5
            assert m.check_rate_limit(1, 1) is False

    def test_expired_timestamps_cleared(self):
        m = make_manager()
        m.request_counts = {1: [time.time() - 61 for _ in range(5)]}
        with patch("modules.ai.chat.config") as mc:
            mc.AI_RATE_LIMIT = 5
            assert m.check_rate_limit(1, 1) is True


class TestAllowlist:
    def test_allow_and_deny(self):
        m = make_manager(allowlist={1: "채널A"})
        assert m.is_chat_allowed(1) is True
        m.deny_chat(1)
        assert m.is_chat_allowed(1) is False

    def test_allow_chat(self):
        m = make_manager()
        m.allow_chat(10, "새 채널")
        assert m.is_chat_allowed(10)
        assert {"id": 10, "name": "새 채널"} in m.list_allowed_chats()

    def test_get_chat_name(self):
        m = make_manager(allowlist={1: "테스트"})
        assert m.get_chat_name(1) == "테스트"
        assert m.get_chat_name(999) == ""


class TestProviderManagement:
    @patch("modules.ai.chat.config")
    def test_switch_provider_unavailable(self, mock_config):
        mock_config.GEMINI_API_KEY = ""
        mock_config.OPENAI_API_KEY = ""
        m = make_manager()
        assert m.switch_provider("gemini") is False

    @patch("modules.ai.chat.Settings")
    @patch("modules.ai.chat.config")
    def test_switch_provider_available(self, mock_config, mock_settings):
        mock_config.GEMINI_API_KEY = "key"
        mock_config.OPENAI_API_KEY = ""
        m = make_manager()
        with patch("modules.ai.chat.GeminiProvider"):
            result = m.switch_provider("gemini")
        assert result is True

    def test_available_providers(self):
        m = make_manager()
        with patch("modules.ai.chat.config") as mc:
            mc.GEMINI_API_KEY = "g-key"
            mc.OPENAI_API_KEY = ""
            providers = m.available_providers()
        assert "gemini" in providers
        assert "openai" not in providers


class TestDelegation:
    def test_set_model_delegates(self):
        provider = make_provider_mock()
        m = make_manager(provider_mock=provider)
        with patch("modules.ai.chat.Settings"):
            m.set_model("new-model")
        provider.set_model.assert_called_once_with("new-model")

    def test_set_search_delegates(self):
        provider = make_provider_mock()
        m = make_manager(provider_mock=provider)
        with patch("modules.ai.chat.Settings"):
            m.set_search(True)
        provider.set_search.assert_called_once_with(True)

    def test_clear_session_delegates(self):
        provider = make_provider_mock()
        m = make_manager(provider_mock=provider)
        m.clear_session(1, 2)
        provider.clear_session.assert_called_once_with((1, 2))

    def test_set_custom_prompt_resets_sessions(self):
        provider = make_provider_mock()
        m = make_manager(provider_mock=provider)
        with patch("modules.ai.chat.Settings"):
            m.set_custom_prompt("Be concise.")
        assert m.custom_prompt == "Be concise."
        provider.reset_sessions.assert_called_once()

    def test_model_property(self):
        provider = make_provider_mock()
        provider.model = "gemini-2.5-pro"
        m = make_manager(provider_mock=provider)
        assert m.model == "gemini-2.5-pro"

    def test_search_enabled_property(self):
        provider = make_provider_mock()
        provider.search_enabled = True
        m = make_manager(provider_mock=provider)
        assert m.search_enabled is True


class TestSplitResponse:
    def test_short_text(self):
        assert AIChatManager.split_response("hello") == ["hello"]

    def test_split_at_newline(self):
        text = "a" * 4000 + "\n" + "b" * 200
        result = AIChatManager.split_response(text)
        assert len(result) == 2
        assert result[0] == "a" * 4000
        assert result[1] == "b" * 200
