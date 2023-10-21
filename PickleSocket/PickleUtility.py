import time
from enum import Enum
from datetime import datetime, timedelta
import logging
from logging.handlers import RotatingFileHandler

# ToDo make thread safe
# ToDo have this class be passed to all classes
# ToDo Should be able to send internal messages with this


class SocketStatus(Enum):
    ERROR = -1
    INIT = 0
    WAITING_FOR_CONNECTION = 1
    WAITING_FOR_HOST = 2
    CONNECTED = 3
    PROCESSING_MESSAGE = 4
    CONNECTION_DEAD = 5


class Utility:

    MESSAGE_TYPE_SIZE = 3
    HEARTBEAT_DELAY = 3.0
    HEARTBEAT_OVERRIDE = 2.0

    NUMBER_ALLOWED_CONNECTIONS = 1
    MESSAGE_CHECK_DELAY = 0.05

    CONNECTION_WAIT_DELAY = 2

    RECEIVED_DATA_SIZE = 1
    RECEIVED_TYPE_SIZE = 2

    MESSAGE_QUEUE_MAX_SIZE = 30

    MAX_HANDSHAKE_COUNT = 10

    SERVER_WAIT_FOR_CONNECTION_DELAY = 2

    SOCKET_LISTEN_TIMEOUT = None
    SOCKET_CONNECTED_TIMEOUT = 0.5

    MESSAGE_SEND_DELAY = 0.0125
    MESSAGE_RECEIVE_DELAY = 0.0125

    @property
    def get_log_level(self):
        return logging.INFO

    @property
    def get_default_time(self):
        return timedelta()

    @staticmethod
    def get_current_time():
        return datetime.now()

    def get_current_time_string(self):
        return str(self.get_current_time())

    def is_default_time(self, ctime):
        return ctime == self.get_default_time

    def set_up_logger_outputs(self, logger_filename):
        console_handler = logging.StreamHandler()
        file_handler = RotatingFileHandler(
            logger_filename, mode='w', maxBytes=(5 * 1024 * 1024),
            encoding=None, backupCount=2, delay=False, errors=None
        )

        console_handler.setLevel(self.get_log_level)
        file_handler.setLevel(self.get_log_level)

        console_format = logging. \
            Formatter("[%(filename)s:%(asctime)s - %(funcName)20s() %(threadName)s]:"
                      "[%(levelname)s-%(lineno)d-%(message)s]")
        file_format = logging. \
            Formatter("[%(filename)s:%(asctime)s - %(funcName)20s() %(threadName)s]:"
                      "[%(levelname)s-%(lineno)d-%(message)s]")

        console_handler.setFormatter(console_format)
        file_handler.setFormatter(file_format)

        return console_handler, file_handler
