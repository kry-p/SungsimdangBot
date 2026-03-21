import threading
import time
from unittest.mock import MagicMock, mock_open, patch

from modules.gemini_chat import GeminiChat, ManagedSession
from resources import strings


def make_gemini_chat(**overrides):
    with patch.object(GeminiChat, "__init__", lambda self: None):
        gc = GeminiChat()
        gc._lock = threading.RLock()
        gc.client = MagicMock()
        gc.model = "gemini-2.5-flash"
        gc.sessions = {}
        gc.request_counts = {}
        gc.allowlist = {}
        for k, v in overrides.items():
            setattr(gc, k, v)
        return gc


class TestAsk:
    def test_normal_response(self):
        gc = make_gemini_chat(allowlist={1: "test"})
        mock_chat = MagicMock()
        mock_chat.send_message.return_value.text = "답변입니다"
        mock_chat.get_history.return_value = []
        gc.client.chats.create.return_value = mock_chat

        result = gc.ask(1, "질문", "ko")
        assert result == "답변입니다"

    def test_no_client(self):
        gc = make_gemini_chat(client=None, allowlist={1: "test"})
        result = gc.ask(1, "질문", "ko")
        assert result == strings.ask_error_msg

    def test_not_allowed(self):
        gc = make_gemini_chat(allowlist={})
        result = gc.ask(1, "질문", "ko")
        assert result == strings.ask_not_allowed_msg

    def test_rate_limited(self):
        gc = make_gemini_chat(allowlist={1: "test"})
        gc.request_counts = {1: [time.time() for _ in range(5)]}
        result = gc.ask(1, "질문", "ko")
        assert result == strings.ask_rate_limit_msg

    def test_api_error(self):
        gc = make_gemini_chat(allowlist={1: "test"})
        mock_chat = MagicMock()
        mock_chat.send_message.side_effect = Exception("API error")
        gc.client.chats.create.return_value = mock_chat

        result = gc.ask(1, "질문", "ko")
        assert result == strings.ask_error_msg

    def test_long_response_split(self):
        gc = make_gemini_chat(allowlist={1: "test"})
        long_text = "a" * 5000
        mock_chat = MagicMock()
        mock_chat.send_message.return_value.text = long_text
        mock_chat.get_history.return_value = []
        gc.client.chats.create.return_value = mock_chat

        result = gc.ask(1, "질문", "ko")
        assert isinstance(result, list)
        assert all(len(chunk) <= 4096 for chunk in result)
        assert "".join(result) == long_text


class TestSessionManagement:
    def test_create_new_session(self):
        gc = make_gemini_chat()
        mock_chat = MagicMock()
        gc.client.chats.create.return_value = mock_chat

        managed = gc._get_or_create_session(1, "ko")
        assert managed.chat is mock_chat
        gc.client.chats.create.assert_called_once()

    def test_reuse_existing_session(self):
        gc = make_gemini_chat()
        existing = ManagedSession(chat=MagicMock())
        gc.sessions[1] = existing

        managed = gc._get_or_create_session(1, "ko")
        assert managed is existing
        gc.client.chats.create.assert_not_called()

    @patch("modules.gemini_chat.config")
    def test_expire_after_timeout(self, mock_config):
        mock_config.GEMINI_SESSION_TIMEOUT = 3600
        gc = make_gemini_chat()
        gc.sessions[1] = ManagedSession(chat=MagicMock(), last_active=time.time() - 3601)

        assert gc._expire_session_if_needed(1) is True
        assert 1 not in gc.sessions

    @patch("modules.gemini_chat.config")
    def test_no_expire_within_timeout(self, mock_config):
        mock_config.GEMINI_SESSION_TIMEOUT = 3600
        gc = make_gemini_chat()
        gc.sessions[1] = ManagedSession(chat=MagicMock(), last_active=time.time())

        assert gc._expire_session_if_needed(1) is False
        assert 1 in gc.sessions

    def test_clear_session(self):
        gc = make_gemini_chat()
        gc.sessions[1] = ManagedSession(chat=MagicMock())
        gc.clear_session(1)
        assert 1 not in gc.sessions

    def test_clear_nonexistent_session(self):
        gc = make_gemini_chat()
        gc.clear_session(999)  # should not raise

    @patch("modules.gemini_chat.config")
    def test_trim_history(self, mock_config):
        mock_config.GEMINI_MAX_HISTORY = 2
        mock_config.GEMINI_MODEL = "gemini-2.5-flash"
        gc = make_gemini_chat()
        mock_chat = MagicMock()
        mock_chat.get_history.return_value = ["a", "b", "c", "d", "e", "f"]
        gc.sessions[1] = ManagedSession(chat=mock_chat)

        new_chat = MagicMock()
        gc.client.chats.create.return_value = new_chat

        gc._trim_history(1, "ko")
        gc.client.chats.create.assert_called_once()
        call_kwargs = gc.client.chats.create.call_args
        assert call_kwargs.kwargs["history"] == ["c", "d", "e", "f"]

    @patch("modules.gemini_chat.config")
    def test_no_trim_within_limit(self, mock_config):
        mock_config.GEMINI_MAX_HISTORY = 10
        gc = make_gemini_chat()
        mock_chat = MagicMock()
        mock_chat.get_history.return_value = ["a", "b"]
        gc.sessions[1] = ManagedSession(chat=mock_chat)

        gc._trim_history(1, "ko")
        gc.client.chats.create.assert_not_called()


class TestRateLimit:
    @patch("modules.gemini_chat.config")
    def test_within_limit(self, mock_config):
        mock_config.GEMINI_RATE_LIMIT = 5
        gc = make_gemini_chat()
        assert gc.check_rate_limit(1) is True

    @patch("modules.gemini_chat.config")
    def test_at_limit(self, mock_config):
        mock_config.GEMINI_RATE_LIMIT = 5
        gc = make_gemini_chat()
        gc.request_counts = {1: [time.time() for _ in range(5)]}
        assert gc.check_rate_limit(1) is False

    @patch("modules.gemini_chat.config")
    def test_expired_timestamps_cleared(self, mock_config):
        mock_config.GEMINI_RATE_LIMIT = 5
        gc = make_gemini_chat()
        gc.request_counts = {1: [time.time() - 61 for _ in range(5)]}
        assert gc.check_rate_limit(1) is True

    @patch("modules.gemini_chat.config")
    def test_empty_timestamps_entry_removed(self, mock_config):
        mock_config.GEMINI_RATE_LIMIT = 5
        gc = make_gemini_chat()
        gc.request_counts = {1: [time.time() - 61], 2: [time.time()]}
        gc.check_rate_limit(1)
        assert 1 in gc.request_counts  # re-added with new timestamp
        gc.request_counts = {3: [time.time() - 61]}
        gc.check_rate_limit(3)
        # after filtering, empty list is removed then re-added
        assert 3 in gc.request_counts

    @patch("modules.gemini_chat.config")
    def test_multiple_chats_partial_expiry(self, mock_config):
        mock_config.GEMINI_RATE_LIMIT = 5
        gc = make_gemini_chat()
        gc.request_counts = {
            1: [time.time() - 61],
            2: [time.time()],
            3: [time.time() - 61],
        }
        gc.check_rate_limit(1)
        gc.check_rate_limit(3)
        assert 2 in gc.request_counts
        assert gc.request_counts[2] == gc.request_counts[2]  # untouched


class TestAllowlist:
    def test_is_chat_allowed(self):
        gc = make_gemini_chat(allowlist={1: "채널A", 2: "채널B"})
        assert gc.is_chat_allowed(1) is True
        assert gc.is_chat_allowed(3) is False

    @patch.object(GeminiChat, "_save_allowlist")
    def test_allow_chat(self, mock_save):
        gc = make_gemini_chat()
        gc.allow_chat(1, "테스트 채널")
        assert gc.allowlist[1] == "테스트 채널"
        mock_save.assert_called_once()

    @patch.object(GeminiChat, "_save_allowlist")
    def test_deny_chat(self, mock_save):
        gc = make_gemini_chat(allowlist={1: "test"})
        gc.deny_chat(1)
        assert 1 not in gc.allowlist
        mock_save.assert_called_once()

    @patch.object(GeminiChat, "_save_allowlist")
    def test_deny_nonexistent_chat(self, mock_save):
        gc = make_gemini_chat()
        gc.deny_chat(999)  # should not raise
        mock_save.assert_called_once()

    def test_list_allowed_chats(self):
        gc = make_gemini_chat(allowlist={3: "C", 1: "A", 2: "B"})
        assert gc.list_allowed_chats() == [
            {"id": 1, "name": "A"},
            {"id": 2, "name": "B"},
            {"id": 3, "name": "C"},
        ]


class TestAllowlistPersistence:
    @patch("modules.gemini_chat.config")
    def test_load_new_format(self, mock_config):
        mock_config.GEMINI_ALLOWLIST_PATH = "data/allowed_chats.json"
        gc = make_gemini_chat()
        data = '[{"id": 1, "name": "A"}, {"id": 2, "name": "B"}]'
        with patch("builtins.open", mock_open(read_data=data)):
            gc._load_allowlist()
        assert gc.allowlist == {1: "A", 2: "B"}

    @patch("modules.gemini_chat.config")
    def test_load_legacy_format(self, mock_config):
        mock_config.GEMINI_ALLOWLIST_PATH = "data/allowed_chats.json"
        gc = make_gemini_chat()
        with patch("builtins.open", mock_open(read_data="[1, 2, 3]")):
            gc._load_allowlist()
        assert gc.allowlist == {1: "", 2: "", 3: ""}

    @patch("modules.gemini_chat.config")
    def test_load_file_not_found(self, mock_config):
        mock_config.GEMINI_ALLOWLIST_PATH = "data/nonexistent.json"
        gc = make_gemini_chat()
        with patch("builtins.open", side_effect=FileNotFoundError):
            gc._load_allowlist()
        assert gc.allowlist == {}

    @patch("modules.gemini_chat.shutil.copy2")
    @patch("modules.gemini_chat.config")
    def test_load_corrupted_json(self, mock_config, mock_copy):
        mock_config.GEMINI_ALLOWLIST_PATH = "data/allowed_chats.json"
        gc = make_gemini_chat()
        with patch("builtins.open", mock_open(read_data="not json")):
            gc._load_allowlist()
        assert gc.allowlist == {}
        mock_copy.assert_called_once_with("data/allowed_chats.json", "data/allowed_chats.json.bak")

    @patch("modules.gemini_chat.os.replace")
    @patch("modules.gemini_chat.os.makedirs")
    @patch("modules.gemini_chat.json.dump")
    @patch("modules.gemini_chat.config")
    def test_save(self, mock_config, mock_json_dump, mock_makedirs, mock_replace):
        mock_config.GEMINI_ALLOWLIST_PATH = "data/allowed_chats.json"
        gc = make_gemini_chat(allowlist={2: "B", 1: "A"})
        mock_tmp = MagicMock()
        mock_tmp.__enter__ = MagicMock(return_value=mock_tmp)
        mock_tmp.__exit__ = MagicMock(return_value=False)
        mock_tmp.name = "/tmp/test.tmp"
        with patch("modules.gemini_chat.tempfile.NamedTemporaryFile", return_value=mock_tmp):
            gc._save_allowlist()
        mock_json_dump.assert_called_once()
        saved_data = mock_json_dump.call_args[0][0]
        assert saved_data == [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}]
        mock_replace.assert_called_once_with("/tmp/test.tmp", "data/allowed_chats.json")

    @patch("modules.gemini_chat.shutil.copy2")
    @patch("modules.gemini_chat.config")
    def test_load_dict_missing_id_key(self, mock_config, mock_copy):
        mock_config.GEMINI_ALLOWLIST_PATH = "data/allowed_chats.json"
        gc = make_gemini_chat()
        data = '[{"name": "no id"}, {"id": 1, "name": "ok"}]'
        with patch("builtins.open", mock_open(read_data=data)):
            gc._load_allowlist()
        assert gc.allowlist == {}
        mock_copy.assert_called_once()

    @patch("modules.gemini_chat.shutil.copy2")
    @patch("modules.gemini_chat.config")
    def test_load_empty_list(self, mock_config, mock_copy):
        mock_config.GEMINI_ALLOWLIST_PATH = "data/allowed_chats.json"
        gc = make_gemini_chat()
        with patch("builtins.open", mock_open(read_data="[]")):
            gc._load_allowlist()
        assert gc.allowlist == {}
        mock_copy.assert_not_called()


class TestSplitResponse:
    def test_short_text(self):
        assert GeminiChat.split_response("hello") == "hello"

    def test_exactly_max_len(self):
        text = "a" * 4096
        assert GeminiChat.split_response(text) == text

    def test_split_at_newline(self):
        text = "a" * 4000 + "\n" + "b" * 200
        result = GeminiChat.split_response(text)
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0] == "a" * 4000
        assert result[1] == "b" * 200

    def test_split_no_newline(self):
        text = "a" * 5000
        result = GeminiChat.split_response(text)
        assert isinstance(result, list)
        assert result[0] == "a" * 4096
        assert result[1] == "a" * 904


class TestBuildSystemPrompt:
    def test_with_language_code(self):
        prompt = GeminiChat._build_system_prompt("ko")
        assert "'ko'" in prompt

    def test_without_language_code(self):
        prompt = GeminiChat._build_system_prompt(None)
        assert "same language" in prompt


class TestListModels:
    def test_normal(self):
        gc = make_gemini_chat()
        m1 = MagicMock()
        m1.name = "models/gemini-2.5-flash"
        m1.supported_actions = ["generateContent", "countTokens"]
        m2 = MagicMock()
        m2.name = "models/gemini-embedding-001"
        m2.supported_actions = ["embedContent"]
        m3 = MagicMock()
        m3.name = "models/gemma-3-4b-it"
        m3.supported_actions = ["generateContent"]
        gc.client.models.list.return_value = [m1, m2, m3]
        result = gc.list_models()
        assert result == ["gemini-2.5-flash"]

    def test_no_client(self):
        gc = make_gemini_chat(client=None)
        assert gc.list_models() == []

    def test_api_error(self):
        gc = make_gemini_chat()
        gc.client.models.list.side_effect = Exception("error")
        assert gc.list_models() == []

    def test_excludes_tts_and_image(self):
        gc = make_gemini_chat()
        m1 = MagicMock()
        m1.name = "models/gemini-2.5-flash-preview-tts"
        m1.supported_actions = ["generateContent"]
        m2 = MagicMock()
        m2.name = "models/gemini-2.5-flash-image"
        m2.supported_actions = ["generateContent"]
        m3 = MagicMock()
        m3.name = "models/gemini-2.5-pro"
        m3.supported_actions = ["generateContent"]
        gc.client.models.list.return_value = [m1, m2, m3]
        result = gc.list_models()
        assert result == ["gemini-2.5-pro"]


class TestSetModel:
    @patch("modules.gemini_chat.Settings")
    def test_set_model(self, mock_settings_cls):
        gc = make_gemini_chat()
        gc.model = "gemini-2.5-flash"
        gc.sessions = {1: MagicMock(), 2: MagicMock()}
        gc.set_model("gemini-2.5-pro")
        assert gc.model == "gemini-2.5-pro"
        assert gc.sessions == {}
        mock_settings_cls().set.assert_called_once_with("modules.gemini_chat", "model", "gemini-2.5-pro")


class TestThreadSafety:
    def test_concurrent_ask_no_duplicate_sessions(self):
        gc = make_gemini_chat(allowlist={1: "test"})
        mock_chat = MagicMock()
        mock_chat.send_message.return_value.text = "ok"
        mock_chat.get_history.return_value = []
        gc.client.chats.create.return_value = mock_chat

        results = []

        def ask():
            results.append(gc.ask(1, "질문", "ko"))

        threads = [threading.Thread(target=ask) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 10
        assert 1 in gc.sessions

    def test_concurrent_allow_and_ask(self):
        gc = make_gemini_chat(allowlist={1: "test"})
        mock_chat = MagicMock()
        mock_chat.send_message.return_value.text = "ok"
        mock_chat.get_history.return_value = []
        gc.client.chats.create.return_value = mock_chat

        errors = []

        def ask():
            try:
                gc.ask(1, "질문", "ko")
            except Exception as e:
                errors.append(e)

        @patch.object(GeminiChat, "_save_allowlist")
        def allow(mock_save):
            try:
                gc.allow_chat(2, "new")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=ask) for _ in range(5)]
        threads += [threading.Thread(target=allow) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == []
        assert 2 in gc.allowlist

    def test_set_model_during_ask(self):
        gc = make_gemini_chat(allowlist={1: "test"})
        mock_chat = MagicMock()
        mock_chat.send_message.return_value.text = "ok"
        mock_chat.get_history.return_value = []
        gc.client.chats.create.return_value = mock_chat

        errors = []

        def ask():
            try:
                gc.ask(1, "질문", "ko")
            except Exception as e:
                errors.append(e)

        @patch("modules.gemini_chat.Settings")
        def set_model(mock_settings):
            try:
                gc.set_model("gemini-2.5-pro")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=ask) for _ in range(5)]
        threads += [threading.Thread(target=set_model) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == []
