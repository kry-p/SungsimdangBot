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
