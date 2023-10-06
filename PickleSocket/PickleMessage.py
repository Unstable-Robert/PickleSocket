from enum import Enum
import logging
from PickleUtility import Utility


class MessageType(Enum):
    INIT = 0
    EXIT = 1
    HEART_BEAT = 2
    SETTINGS = 9
    MSG = 10    # server key is contents
    IMAGE = 11    # server key is contents
    MOTOR = 12
    GPS_DATA = 13

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return self.value == other

    def __ne__(self, other):
        # not needed in Python 3
        return self.value != other


class Message(object):

    def __init__(self, stype: MessageType = None, contents=None, size=-1):
        self.util = Utility()

        logger_name = "message_" + __name__

        self.logger = logging.getLogger(logger_name)

        if not self.logger.hasHandlers():
            console_handler, file_handler = self.util.set_up_logger_outputs(logger_name + '.log')

            self.logger.addHandler(console_handler)
            self.logger.addHandler(file_handler)

        self.logger.setLevel(self.util.get_log_level())

        self.image_data = b''

        message_len = size
        if message_len == -1:
            message_len = len(contents)
        self.type = stype
        self.contents = contents
        self.size = message_len

        return

    def __getstate__(self):
        """
        used by pickle to serialize data
        :return:
        """
        state = self.__dict__.copy()
        del state["logger"]
        # if self.stype == MessageType.IMAGE:
        #     state["contents"] = pickle.dumps(self.contents, 0)
        return state

    def __setstate__(self, state):
        """
        used by pickle to create object
        :param state:
        :return:
        """
        self.__dict__.update(state)
        logger_filename = "message_" + __name__ + '.log'

        self.logger = logging.getLogger(__name__)

        if not self.logger.hasHandlers():
            console_handler, file_handler = self.util.set_up_logger_outputs(logger_filename)

            self.logger.addHandler(console_handler)
            self.logger.addHandler(file_handler)

        self.logger.setLevel(self.util.get_log_level())
