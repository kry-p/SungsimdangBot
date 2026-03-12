from unittest.mock import patch

from modules.log import Logger


class TestLoggerInit:
    @patch("modules.log.os.makedirs")
    @patch("modules.log.os.path.exists", return_value=False)
    def test_normal_init(self, _mock_exists, _mock_makedirs):
        logger = Logger()
        assert hasattr(logger, "logger")
        assert hasattr(logger, "stream_handler")


class TestLoggerInitFallback:
    @patch("modules.log.Logger.create_directory", return_value=False)
    def test_fallback_console_only(self, _mock_create):
        logger = Logger()
        assert hasattr(logger, "logger")
        assert hasattr(logger, "stream_handler")
        assert not hasattr(logger, "timed_file_handler")


class TestCreateDirectory:
    @patch("modules.log.os.makedirs", side_effect=OSError("permission denied"))
    @patch("modules.log.os.path.exists", return_value=False)
    def test_oserror_returns_false(self, _mock_exists, _mock_makedirs, capsys):
        logger = Logger.__new__(Logger)
        result = logger.create_directory("/fake/path")
        assert result is False
        captured = capsys.readouterr()
        assert "Failed to create the directory" in captured.out


class TestLogMethods:
    @patch("modules.log.Logger.create_directory", return_value=False)
    def test_log_info(self, _mock_create):
        logger = Logger()
        with patch.object(logger.logger, "info") as mock_info:
            logger.log_info("test message")
            mock_info.assert_called_once_with("test message")

    @patch("modules.log.Logger.create_directory", return_value=False)
    def test_log_error(self, _mock_create):
        logger = Logger()
        with patch.object(logger.logger, "error") as mock_error:
            logger.log_error("error message")
            mock_error.assert_called_once_with("error message")
