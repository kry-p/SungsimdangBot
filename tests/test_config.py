import importlib
from unittest.mock import patch

from config.config import _int_env


class TestIntEnv:
    @patch.dict("os.environ", {"TEST_KEY": "42"})
    def test_normal_value(self):
        assert _int_env("TEST_KEY", 0) == 42

    @patch.dict("os.environ", {"TEST_KEY": ""})
    def test_empty_string_returns_default(self):
        assert _int_env("TEST_KEY", 99) == 99

    @patch.dict("os.environ", {}, clear=True)
    def test_missing_key_returns_default(self):
        assert _int_env("NONEXISTENT_KEY", 77) == 77

    @patch.dict("os.environ", {"TEST_KEY": "0"})
    def test_zero_value(self):
        assert _int_env("TEST_KEY", 99) == 0

    @patch.dict("os.environ", {"TEST_KEY": "-5"})
    def test_negative_value(self):
        assert _int_env("TEST_KEY", 0) == -5


class TestOpenAIBaseURL:
    def _reload(self):
        import config.config as c

        importlib.reload(c)
        return c

    def test_custom_url(self):
        with patch.dict("os.environ", {"OPENAI_BASE_URL": "https://custom.api.com/v1"}):
            c = self._reload()
            assert c.OPENAI_BASE_URL == "https://custom.api.com/v1"

    def test_empty_string_falls_back_to_default(self):
        with patch.dict("os.environ", {"OPENAI_BASE_URL": ""}):
            c = self._reload()
            assert c.OPENAI_BASE_URL == "https://api.openai.com/v1"

    def test_missing_key_falls_back_to_default(self):
        with patch.dict("os.environ", {}, clear=True):
            c = self._reload()
            assert c.OPENAI_BASE_URL == "https://api.openai.com/v1"
