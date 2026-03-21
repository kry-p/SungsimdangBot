import threading
from unittest.mock import MagicMock, mock_open, patch

from modules.settings import Settings


def reset_singleton():
    Settings._instance = None


class TestSingleton:
    def test_same_instance(self):
        reset_singleton()
        with patch.object(Settings, "_load"):
            s1 = Settings()
            s2 = Settings()
            assert s1 is s2
        reset_singleton()


class TestGetSet:
    def test_get_default(self):
        reset_singleton()
        with patch.object(Settings, "_load"):
            s = Settings()
            s._data = {}
            assert s.get("modules.gemini_chat", "model", "default") == "default"
        reset_singleton()

    def test_set_and_get(self):
        reset_singleton()
        with patch.object(Settings, "_load"), patch.object(Settings, "_save"):
            s = Settings()
            s._data = {}
            s.set("modules.gemini_chat", "model", "gemini-2.5-pro")
            assert s.get("modules.gemini_chat", "model") == "gemini-2.5-pro"
            assert s._data == {"modules": {"gemini_chat": {"model": "gemini-2.5-pro"}}}
        reset_singleton()

    def test_get_nonexistent_path(self):
        reset_singleton()
        with patch.object(Settings, "_load"):
            s = Settings()
            s._data = {}
            assert s.get("modules.nonexistent", "key") is None
        reset_singleton()

    def test_set_preserves_existing(self):
        reset_singleton()
        with patch.object(Settings, "_load"), patch.object(Settings, "_save"):
            s = Settings()
            s._data = {"modules": {"other": {"key": "value"}}}
            s.set("modules.gemini_chat", "model", "gemini-2.5-flash")
            assert s._data["modules"]["other"]["key"] == "value"
            assert s._data["modules"]["gemini_chat"]["model"] == "gemini-2.5-flash"
        reset_singleton()


class TestPersistence:
    def test_load_success(self):
        reset_singleton()
        data = '{"modules": {"gemini_chat": {"model": "gemini-2.5-pro"}}}'
        with patch("builtins.open", mock_open(read_data=data)):
            s = Settings()
            assert s.get("modules.gemini_chat", "model") == "gemini-2.5-pro"
        reset_singleton()

    def test_load_file_not_found(self):
        reset_singleton()
        with patch("builtins.open", side_effect=FileNotFoundError):
            s = Settings()
            assert s._data == {}
        reset_singleton()

    @patch("modules.settings.shutil.copy2")
    def test_load_corrupted_json(self, mock_copy):
        reset_singleton()
        with patch("builtins.open", mock_open(read_data="not json")):
            s = Settings()
            assert s._data == {}
            mock_copy.assert_called_once()
        reset_singleton()


class TestSave:
    @patch("modules.settings.os.replace")
    @patch("modules.settings.os.makedirs")
    @patch("modules.settings.json.dump")
    def test_save_writes_json(self, mock_json_dump, mock_makedirs, mock_replace):
        reset_singleton()
        with patch.object(Settings, "_load"):
            s = Settings()
            s._data = {"modules": {"gemini_chat": {"model": "gemini-2.5-pro"}}}
            mock_tmp = MagicMock()
            mock_tmp.__enter__ = MagicMock(return_value=mock_tmp)
            mock_tmp.__exit__ = MagicMock(return_value=False)
            mock_tmp.name = "/tmp/test.tmp"
            with patch("modules.settings.tempfile.NamedTemporaryFile", return_value=mock_tmp):
                s._save()
            mock_json_dump.assert_called_once()
            saved_data = mock_json_dump.call_args[0][0]
            assert saved_data == {"modules": {"gemini_chat": {"model": "gemini-2.5-pro"}}}
            mock_replace.assert_called_once()
        reset_singleton()

    @patch("modules.settings.os.replace")
    @patch("modules.settings.os.makedirs")
    @patch("modules.settings.json.dump")
    def test_save_uses_temp_file_then_replace(self, mock_json_dump, mock_makedirs, mock_replace):
        reset_singleton()
        with patch.object(Settings, "_load"):
            s = Settings()
            s._data = {"key": "value"}
            mock_tmp = MagicMock()
            mock_tmp.__enter__ = MagicMock(return_value=mock_tmp)
            mock_tmp.__exit__ = MagicMock(return_value=False)
            mock_tmp.name = "/tmp/settings.tmp"
            with patch("modules.settings.tempfile.NamedTemporaryFile", return_value=mock_tmp):
                s._save()
            mock_json_dump.assert_called_once_with({"key": "value"}, mock_tmp)
            mock_replace.assert_called_once_with("/tmp/settings.tmp", "data/settings.json")
        reset_singleton()


class TestThreadSafety:
    def test_concurrent_singleton_creation(self):
        reset_singleton()
        instances = []

        def create():
            with patch.object(Settings, "_load"):
                instances.append(Settings())

        threads = [threading.Thread(target=create) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert all(inst is instances[0] for inst in instances)
        reset_singleton()

    def test_concurrent_set_and_get(self):
        reset_singleton()
        with patch.object(Settings, "_load"), patch.object(Settings, "_save"):
            s = Settings()
            s._data = {}
            errors = []

            def setter(i):
                try:
                    s.set("modules.test", "key", i)
                except Exception as e:
                    errors.append(e)

            def getter():
                try:
                    s.get("modules.test", "key", None)
                except Exception as e:
                    errors.append(e)

            threads = [threading.Thread(target=setter, args=(i,)) for i in range(10)]
            threads += [threading.Thread(target=getter) for _ in range(10)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            assert errors == []
            assert s.get("modules.test", "key") is not None
        reset_singleton()
