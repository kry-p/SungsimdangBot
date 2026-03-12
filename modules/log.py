import datetime
import logging
import logging.handlers
import os

LOG_DIRECTORY = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "log")


class Logger:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")

        self.streamHandler = logging.StreamHandler()
        self.streamHandler.setFormatter(self.formatter)
        self.logger.addHandler(self.streamHandler)

        is_success = self.create_directory(LOG_DIRECTORY)
        if not is_success:
            return

        self.fileHandler = logging.FileHandler(
            f"{LOG_DIRECTORY}/logfile_{datetime.datetime.now():%Y%m%d}.log", encoding="utf-8"
        )
        self.timedFileHandler = logging.handlers.TimedRotatingFileHandler(
            filename="logfile", when="midnight", interval=1, encoding="utf-8"
        )
        self.timedFileHandler.setFormatter(self.formatter)
        self.timedFileHandler.suffix = "%Y%m%d"
        self.logger.addHandler(self.timedFileHandler)

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
