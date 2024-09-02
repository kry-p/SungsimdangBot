import os
import datetime
import logging
import logging.handlers

LOG_DIRECTORY = '../log'

class Logger: 
    def __init__(self):
        isSuccess = self.create_directory(LOG_DIRECTORY)
        if isSuccess != True:
            return
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
        self.fileHandler = logging.FileHandler("{}/logfile_{:%Y%m%d}.log".format(LOG_DIRECTORY, datetime.datetime.now()),
                                            encoding="utf-8")
        self.streamHandler = logging.StreamHandler()
        self.streamHandler.setFormatter(self.formatter)
        self.logger.addHandler(self.streamHandler)

        self.timedFileHandler = logging.handlers.TimedRotatingFileHandler(filename='logfile',
                                                                        when='midnight',
                                                                        interval=1,
                                                                        encoding='utf-8')
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
        logging.info(message)

    def log_error(self, message):
        logging.error(message)