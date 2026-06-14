import threading
import time
from unittest.mock import MagicMock, patch

import pytest

from modules.ai.providers.base import AIClientError, AIServerError
from modules.ai.providers.openai import OpenAIProvider


def make_provider(**kwargs):
    with patch.object(OpenAIProvider, "__init__", lambda self, **kw: None):
        p = OpenAIProvider()
        p._lock = threading.RLock()
        p.client = MagicMock()
        p.model = "gpt-4o"
        p.search_enabled = False
        p.sessions = {}
        for k, v in kwargs.items():
            setattr(p, k, v)
    return p


class TestAsk:
    def test_normal_response(self):
        p = make_provider()
        p.client.responses.create.return_value.output_text = "답변"

        result = p.ask((1, 1), "system", "질문")
        assert result == "답변"

    def test_no_client_raises(self):
        p = make_provider(client=None)
        with pytest.raises(AIClientError):
            p.ask((1, 1), "system", "질문")

    def test_api_error_raises(self):
        import openai

        p = make_provider()
        p.client.responses.create.side_effect = openai.APIStatusError(
            "error", response=MagicMock(status_code=429), body={}
        )
        with pytest.raises(AIClientError):
            p.ask((1, 1), "system", "질문")

    def test_server_error_raises(self):
        import openai

        p = make_provider()
        p.client.responses.create.side_effect = openai.APIStatusError(
            "error", response=MagicMock(status_code=500), body={}
        )
        with pytest.raises(AIServerError):
            p.ask((1, 1), "system", "질문")

    def test_timeout_raises(self):
        import openai

        p = make_provider()
        p.client.responses.create.side_effect = openai.APITimeoutError(request=MagicMock())
        with pytest.raises(TimeoutError):
            p.ask((1, 1), "system", "질문")

    def test_with_image(self):
        p = make_provider()
        p.client.responses.create.return_value.output_text = "이미지 설명"
        image_data = b"fake_image"

        result = p.ask((1, 1), "system", "이게 뭐야", image=image_data)
        assert result == "이미지 설명"
        call_input = p.client.responses.create.call_args.kwargs["input"]
        user_msg = call_input[0]
        assert isinstance(user_msg["content"], list)
        assert any(item.get("type") == "input_image" for item in user_msg["content"])

    def test_search_enabled_passes_tool(self):
        p = make_provider(search_enabled=True)
        p.client.responses.create.return_value.output_text = "답변"

        p.ask((1, 1), "system", "질문")
        tools = p.client.responses.create.call_args.kwargs.get("tools", [])
        assert any(t.get("type") == "web_search_preview" for t in tools)

    def test_search_disabled_no_tool(self):
        p = make_provider(search_enabled=False)
        p.client.responses.create.return_value.output_text = "답변"

        p.ask((1, 1), "system", "질문")
        tools = p.client.responses.create.call_args.kwargs.get("tools", [])
        assert tools == []

    def test_history_maintained(self):
        p = make_provider()
        p.client.responses.create.return_value.output_text = "답변"

        p.ask((1, 1), "sys", "첫 번째 질문")
        p.ask((1, 1), "sys", "두 번째 질문")

        session = p.sessions[(1, 1)]
        assert len(session.messages) == 4  # user1, assistant1, user2, assistant2

    def test_separate_sessions_per_key(self):
        p = make_provider()
        p.client.responses.create.return_value.output_text = "ok"

        p.ask((1, 1), "sys", "q1")
        p.ask((1, 2), "sys", "q2")

        assert (1, 1) in p.sessions
        assert (1, 2) in p.sessions

    @patch("modules.ai.providers.openai.config")
    def test_history_trimmed(self, mock_config):
        mock_config.AI_MAX_HISTORY = 2
        mock_config.AI_API_TIMEOUT = 60
        p = make_provider()
        p.client.responses.create.return_value.output_text = "ok"
        from modules.ai.providers.openai import OpenAISession

        p.sessions[(1, 1)] = OpenAISession(
            messages=[
                {"role": "user", "content": "q1"},
                {"role": "assistant", "content": "a1"},
                {"role": "user", "content": "q2"},
                {"role": "assistant", "content": "a2"},
                {"role": "user", "content": "q3"},
                {"role": "assistant", "content": "a3"},
            ]
        )
        p.ask((1, 1), "sys", "q4")
        session = p.sessions[(1, 1)]
        # Should trim to AI_MAX_HISTORY * 2 = 4 entries + new exchange
        assert len(session.messages) <= (mock_config.AI_MAX_HISTORY * 2) + 2


class TestSessionManagement:
    def test_clear_session(self):
        p = make_provider()
        p.sessions[(1, 1)] = MagicMock()
        p.clear_session((1, 1))
        assert (1, 1) not in p.sessions

    def test_reset_sessions(self):
        p = make_provider()
        p.sessions = {(1, 1): MagicMock(), (2, 2): MagicMock()}
        p.reset_sessions()
        assert p.sessions == {}

    def test_cleanup_expired(self):
        p = make_provider()
        from modules.ai.providers.openai import OpenAISession

        p.sessions = {
            (1, 1): OpenAISession(messages=[], last_active=time.time() - 7200),
            (2, 2): OpenAISession(messages=[], last_active=time.time()),
        }
        p.cleanup_expired(3600)
        assert (1, 1) not in p.sessions
        assert (2, 2) in p.sessions


class TestModelAndSearch:
    def test_set_model_clears_sessions(self):
        p = make_provider()
        p.sessions = {(1, 1): MagicMock()}
        p.set_model("gpt-4o-mini")
        assert p.model == "gpt-4o-mini"
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

    def test_list_models(self):
        p = make_provider()
        ids = [
            "gpt-4o",
            "gpt-4o-mini",
            "o3-mini",
            "gpt-4-turbo",
            "text-embedding-ada-002",
            "dall-e-3",
            "whisper-1",
            "tts-1",
            "gpt-4o-audio-preview",
            "gpt-4o-realtime-preview",
            "gpt-image-1",
            "gpt-4o-2024-05-13",
            "gpt-4-0613",
            "gpt-4-1106-preview",
            "gpt-3.5-turbo-instruct",
            "gpt-4-turbo-preview",
        ]
        p.client.models.list.return_value = [MagicMock(id=i) for i in ids]
        result = p.list_models()
        assert "gpt-4o" in result
        assert "gpt-4o-mini" in result
        assert "o3-mini" in result
        assert "gpt-4-turbo" in result
        assert "text-embedding-ada-002" not in result
        assert "dall-e-3" not in result
        assert "whisper-1" not in result
        assert "tts-1" not in result
        assert "gpt-4o-audio-preview" not in result
        assert "gpt-4o-realtime-preview" not in result
        assert "gpt-image-1" not in result
        assert "gpt-4o-2024-05-13" not in result
        assert "gpt-4-0613" not in result
        assert "gpt-4-1106-preview" not in result
        assert "gpt-3.5-turbo-instruct" not in result
        assert "gpt-4-turbo-preview" not in result

    def test_list_models_no_client(self):
        p = make_provider(client=None)
        assert p.list_models() == []

    def test_list_models_api_error(self):
        p = make_provider()
        p.client.models.list.side_effect = Exception("error")
        assert p.list_models() == []
