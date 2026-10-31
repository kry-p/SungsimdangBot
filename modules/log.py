import logging
import logging.handlers
import os

LOG_DIRECTORY = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "log")
_HANDLER_KIND_ATTRIBUTE = "_sungsimdangbot_handler_kind"
_STREAM_HANDLER_KIND = "stream"
_TIMED_FILE_HANDLER_KIND = "timed_file"


class Logger:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False
        self.formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")

        self.stream_handler = self._find_handler(_STREAM_HANDLER_KIND)
        if self.stream_handler is None:
            self.stream_handler = logging.StreamHandler()
            setattr(self.stream_handler, _HANDLER_KIND_ATTRIBUTE, _STREAM_HANDLER_KIND)
            self.stream_handler.setFormatter(self.formatter)
            self.logger.addHandler(self.stream_handler)

        is_success = self.create_directory(LOG_DIRECTORY)
        if not is_success:
            return

        self.timed_file_handler = self._find_handler(_TIMED_FILE_HANDLER_KIND)
        if self.timed_file_handler is None:
            self.timed_file_handler = logging.handlers.TimedRotatingFileHandler(
                filename=f"{LOG_DIRECTORY}/logfile", when="midnight", interval=1, encoding="utf-8"
            )
            setattr(self.timed_file_handler, _HANDLER_KIND_ATTRIBUTE, _TIMED_FILE_HANDLER_KIND)
            self.timed_file_handler.setFormatter(self.formatter)
            self.timed_file_handler.suffix = "%Y%m%d"
            self.logger.addHandler(self.timed_file_handler)

    def _find_handler(self, kind):
        return next(
            (handler for handler in self.logger.handlers if getattr(handler, _HANDLER_KIND_ATTRIBUTE, None) == kind),
            None,
        )

    def create_directory(self, directory):
        try:
            if not os.path.exists(directory):
                os.makedirs(directory)
            return True
        except OSError:
            print("Error: Failed to create the directory.")
            return False

    def log_info(self, message):
        self.logger.info(message)

    def log_error(self, message):
        self.logger.error(message)

    def add_file_handler_to(self, target_logger):
        file_handler = getattr(self, "timed_file_handler", None)
        if file_handler is not None and file_handler not in target_logger.handlers:
            target_logger.addHandler(file_handler)
