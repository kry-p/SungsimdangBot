from unittest.mock import patch

from modules.log import Logger


class TestLoggerInit:
    @patch("modules.log.os.makedirs")
    @patch("modules.log.os.path.exists", return_value=False)
    def test_normal_init(self, _mock_exists, _mock_makedirs):
        logger = Logger()
        assert hasattr(logger, "logger")
        assert hasattr(logger, "streamHandler")


class TestLoggerInitFallback:
    @patch("modules.log.Logger.create_directory", return_value=False)
    def test_fallback_console_only(self, _mock_create):
        logger = Logger()
        assert hasattr(logger, "logger")
        assert hasattr(logger, "streamHandler")
        assert not hasattr(logger, "timedFileHandler")


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
