import json
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


def parse_log_calls(mock_method):
    return [json.loads(call.args[0]) for call in mock_method.call_args_list]


class TestAsk:
    def test_normal_response(self):
        p = make_provider()
        response = p.client.responses.create.return_value
        response.output_text = "답변"
        response.id = "resp_test"
        response._request_id = "req_test"
        response.status = "completed"
        response.output = [MagicMock(type="message")]

        with patch("modules.ai.providers.openai.logger") as mock_logger:
            result = p.ask((1, 1), "system", "질문")

        assert result == "답변"
        events = parse_log_calls(mock_logger.log_info)
        assert [event["event"] for event in events] == [
            "ai.openai.request_started",
            "ai.openai.request_succeeded",
        ]
        assert events[1]["request_id"] == "req_test"
        assert events[1]["response_id"] == "resp_test"
        assert events[1]["output_item_types"] == ["message"]
        assert "질문" not in mock_logger.log_info.call_args.args[0]

    def test_no_client_raises(self):
        p = make_provider(client=None)
        with pytest.raises(AIClientError):
            p.ask((1, 1), "system", "질문")

    def test_api_error_raises(self):
        import openai

        p = make_provider()
        error_response = MagicMock(status_code=429, headers={"x-request-id": "req_rate_limit"})
        p.client.responses.create.side_effect = openai.APIStatusError(
            "error",
            response=error_response,
            body={"error": {"type": "rate_limit_error", "code": "rate_limit_exceeded"}},
        )
        with patch("modules.ai.providers.openai.logger") as mock_logger, pytest.raises(AIClientError):
            p.ask((1, 1), "system", "질문")

        event = parse_log_calls(mock_logger.log_exception)[0]
        assert event["stage"] == "api_call"
        assert event["error_category"] == "rate_limit"
        assert event["status_code"] == 429
        assert event["error_type"] == "rate_limit_error"
        assert event["error_code"] == "rate_limit_exceeded"

    def test_server_error_raises(self):
        import openai

        p = make_provider()
        p.client.responses.create.side_effect = openai.APIStatusError(
            "error", response=MagicMock(status_code=500), body={}
        )
        with pytest.raises(AIServerError):
            p.ask((1, 1), "system", "질문")

    def test_connection_error_is_logged_and_raises(self):
        import openai

        p = make_provider()
        p.client.responses.create.side_effect = openai.APIConnectionError(request=MagicMock())

        with patch("modules.ai.providers.openai.logger") as mock_logger, pytest.raises(AIServerError):
            p.ask((1, 1), "system", "질문")

        event = parse_log_calls(mock_logger.log_exception)[0]
        assert event["stage"] == "api_call"
        assert event["error_category"] == "connection"

    def test_timeout_raises(self):
        import openai

        p = make_provider()
        p.client.responses.create.side_effect = openai.APITimeoutError(request=MagicMock())
        with patch("modules.ai.providers.openai.logger") as mock_logger, pytest.raises(TimeoutError):
            p.ask((1, 1), "system", "질문")

        event = parse_log_calls(mock_logger.log_exception)[0]
        assert event["stage"] == "api_call"
        assert event["error_category"] == "timeout"

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

    def test_empty_output_text_raises_and_clears_user_message(self):
        p = make_provider()
        response = p.client.responses.create.return_value
        response.output_text = None
        response.id = "resp_empty"
        response._request_id = "req_empty"
        response.status = "completed"
        response.output = [MagicMock(type="reasoning")]

        with patch("modules.ai.providers.openai.logger") as mock_logger, pytest.raises(AIServerError):
            p.ask((1, 1), "system", "질문")

        session = p.sessions.get((1, 1))
        assert session is None or len(session.messages) == 0
        event = parse_log_calls(mock_logger.log_error)[0]
        assert event["event"] == "ai.openai.response_invalid"
        assert event["stage"] == "response_extract"
        assert event["output_text_present"] is False
        assert event["response_id"] == "resp_empty"

    def test_sdk_response_parsing_error_is_logged_without_sensitive_values(self):
        p = make_provider()
        question = "비밀 질문"
        p.client.responses.create.side_effect = AttributeError(
            f"{question}: typing.Union failed with sk-test-secret and Bearer private-token"
        )

        with patch("modules.ai.providers.openai.logger") as mock_logger, pytest.raises(AIServerError):
            p.ask((1, 1), "system", question)

        serialized = mock_logger.log_exception.call_args.args[0]
        event = json.loads(serialized)
        assert event["stage"] == "sdk_response_parse"
        assert event["error_category"] == "sdk_response_parse"
        assert event["exception_type"] == "AttributeError"
        assert question not in serialized
        assert "sk-test-secret" not in serialized
        assert "private-token" not in serialized
        assert p.sessions[(1, 1)].messages == []

    def test_output_text_accessor_error_is_logged(self):
        class BrokenResponse:
            id = "resp_broken"
            _request_id = "req_broken"
            status = "completed"
            output = []
            error = None
            incomplete_details = None

            @property
            def output_text(self):
                raise ValueError("output accessor failed")

        p = make_provider()
        p.client.responses.create.return_value = BrokenResponse()

        with patch("modules.ai.providers.openai.logger") as mock_logger, pytest.raises(AIServerError):
            p.ask((1, 1), "system", "질문")

        event = parse_log_calls(mock_logger.log_exception)[0]
        assert event["event"] == "ai.openai.postprocess_failed"
        assert event["stage"] == "response_extract"
        assert event["request_id"] == "req_broken"
        assert len(p.sessions[(1, 1)].messages) == 1

    def test_history_trim_error_is_logged(self):
        p = make_provider()
        p.client.responses.create.return_value.output_text = "답변"
        p._trim_history = MagicMock(side_effect=RuntimeError("trim failed"))

        with patch("modules.ai.providers.openai.logger") as mock_logger, pytest.raises(AIServerError):
            p.ask((1, 1), "system", "질문")

        event = parse_log_calls(mock_logger.log_exception)[0]
        assert event["event"] == "ai.openai.postprocess_failed"
        assert event["stage"] == "history_trim"
        assert len(p.sessions[(1, 1)].messages) == 2

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
            # 포함돼야 하는 것
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-3.5-turbo",
            "o1",
            "o1-mini",
            "o3",
            "o3-mini",
            "o4-mini",
            "chatgpt-4o-latest",
            # 제외돼야 하는 것 — 비텍스트 계열
            "text-embedding-ada-002",
            "dall-e-3",
            "whisper-1",
            "tts-1",
            "babbage-002",
            "davinci-002",
            # 제외돼야 하는 것 — gpt- 내 특수 기능
            "gpt-4o-audio-preview",
            "gpt-4o-realtime-preview",
            "gpt-image-1",
            # 제외돼야 하는 것 — 날짜 버전 / preview / instruct
            "gpt-4o-2024-05-13",
            "gpt-4-0613",
            "gpt-4-1106-preview",
            "gpt-3.5-turbo-instruct",
            "gpt-4-turbo-preview",
        ]
        p.client.models.list.return_value = [MagicMock(id=i) for i in ids]
        result = p.list_models()
        for m in (
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-3.5-turbo",
            "o1",
            "o1-mini",
            "o3",
            "o3-mini",
            "o4-mini",
            "chatgpt-4o-latest",
        ):
            assert m in result, f"{m} should be included"
        for m in (
            "text-embedding-ada-002",
            "dall-e-3",
            "whisper-1",
            "tts-1",
            "babbage-002",
            "davinci-002",
            "gpt-4o-audio-preview",
            "gpt-4o-realtime-preview",
            "gpt-image-1",
            "gpt-4o-2024-05-13",
            "gpt-4-0613",
            "gpt-4-1106-preview",
            "gpt-3.5-turbo-instruct",
            "gpt-4-turbo-preview",
        ):
            assert m not in result, f"{m} should be excluded"

    def test_list_models_no_client(self):
        p = make_provider(client=None)
        assert p.list_models() == []

    def test_list_models_api_error(self):
        p = make_provider()
        p.client.models.list.side_effect = Exception("error")
        assert p.list_models() == []
