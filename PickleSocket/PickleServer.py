import queue
import socket
import threading
import time
import logging
import struct
import pickle

from PickleUtility import SocketStatus
from PickleUtility import Utility
from PickleMessage import MessageType
from PickleMessage import Message


class PickleServer:
    """
    Host server for clients to connect too
    Manages receiver and sending threads
    Server thread reconnects on failure
    """

    def __init__(self, name, ip, port, network_key="key"):

        self.network_status = SocketStatus.INIT

        self.util = Utility()

        self.network_name = name
        self.network_key = network_key

        self.network_ip = ip
        self.network_port = port

        logger_name = self.network_name + __name__

        self.logger = logging.getLogger(logger_name)

        if not self.logger.hasHandlers():
            console_handler, file_handler = self.util.set_up_logger_outputs(logger_name + ".log")

            self.logger.addHandler(console_handler)
            self.logger.addHandler(file_handler)

        self.logger.setLevel(self.util.get_log_level())

        self.network_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.network_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.time_last_hrb_sent = None
        self.time_last_msg_sent = None
        self.time_last_msg_recv = None

        self.last_msg_recv = queue.Queue()
        self.last_msg_sent = queue.Queue()

        self.next_msg_sent = queue.Queue()

        self.manage_thread = threading.Thread(target=None, daemon=True)
        self.producer_thread = threading.Thread(target=None, daemon=True)
        self.consumer_thread = threading.Thread(target=None, daemon=True)

        self.connection_alive = False
        self.manage_alive = True

        # ToDo double check if this should be self or only in get_object
        self.recv_data = b""
        self.payload_size = struct.calcsize(">L")

    def connection_status(self):
        """
        Summary and current status of connection.
        :return: Formatted string with ip, port, connected, current state
        """
        s_status = f"Socket - {self.network_ip}:{self.network_port}\n" \
                   f"Status: {self.network_status}\n" \
                   f"Connected:{self.connection_alive}\n"
        return s_status

    def _consumer_producer_init(self):
        """
        Consumer producer thread init
        """
        self.producer_thread = threading.Thread(target=None, daemon=True)
        self.consumer_thread = threading.Thread(target=None, daemon=True)

    def start_server(self):
        """
        Start the manage thread to wait for a connection
        """
        try:
            if not self.manage_thread.isAlive():
                self.manage_thread.start()
            else:
                pass
        except threading.ThreadError:
            pass

    def _start_consumer_producer_pair(self):
        """
        Checks to make sure the connection is alive.
        Starts both consumer and producer threads to handle
        sending and receiving message
        :return:
        """

        try:
            if self.connection_alive:
                self.network_status = SocketStatus.CONNECTED
                self.producer_thread.start()
                self.consumer_thread.start()
            else:
                pass
        except threading.ThreadError:
            try:
                self._consumer_producer_init()
                self.network_status = SocketStatus.CONNECTED
                self.producer_thread.start()
                self.consumer_thread.start()
            except threading.ThreadError:
                pass

    def _should_reset_queue(self, to_test):
        """
        checks to make sure queue is smaller than max set
        in utility class
        :param to_test:
        :return:
        """
        pass

    def _queue_last_msg_recv(self, message):
        """
        queue message to last_msg_recv
        :param message:
        :return:
        """
        pass

    def _queue_last_msg_sent(self, message):
        """
        queue message to last_msg_sent
        :param message:
        :return:
        """
        pass

    def _queue_next_msg_sent(self, message):
        """
        queue message to next next_msg_sent
        :param message:
        :return:
        """
        pass

    def wait_for_client(self):
        """
        Waits for one socket timeout
        :return: bool on connection success
        """
        pass

    def _client_handshake(self):
        """
        handles initial handshake
        exchanges network key with client
        sets connection_alive true
        :return: bool on key success
        """
        pass

    def disconnect_from_client(self):
        """
        sends disconnect message to client
        waits
        :return:
        """
        pass

    def _client_disconnect_from_server(self):
        """
        handles closing the connection at the clients request
        :return:
        """
        pass

    def _send_object(self, message):
        """
        sends a single message over the socket
        :param message:
        :return:
        """
        try:
            data_to_send = pickle.dumps(message, 0)
            data_size = len(data_to_send)

            self.logger.info(f"message send size: {data_size}")

            self.network_socket.sendall(struct.pack(">L", data_size) + data_to_send)
            self.time_since_last_msg_sent = self.util.get_current_time()
        except socket.error:
            self.logger.error("Socket error when sending object")

    def _get_object(self):
        """
        gets a single message from the socket
        :return:
        """
        try:

            while len(self.recv_data) < self.payload_size:
                self.recv_data += self.network_socket.recv(4096)

            # self.logger.debug(f"Done RECV: {len(self.data)}")
            packed_msg_size = self.recv_data[:self.payload_size]

            self.data = self.recv_data[self.payload_size:]

            msg_size = struct.unpack(">L", packed_msg_size)[0]

            # self.logger.debug(f"msg size: {msg_size}")

            while len(self.data) < msg_size:
                # self.logger.debug(f"Data size: {len(self.data)}")
                self.data += self.network_socket.recv(4096)

            message_str = self.data[:msg_size]

            self.data = self.data[msg_size:]

            message = pickle.loads(message_str, fix_imports=True, encoding="bytes")

            self.logger.debug(f"Encoded Type: {type(message)}")

            self.time_since_last_msg_received = self.util.get_current_time()

            if message.type == MessageType.HEART_BEAT:
                self._got_heartbeat(message)
                return None
            return message
        except socket.timeout as e:
            self.logger.debug(f"No data on socket Error: {e}")
        except socket.error as e:
            self.logger.error(f"Error when getting object Error:{e}")
        except BaseException as e:
            self.logger.error(f"unknown error must handle Error {e}")

    def queue_next_message_send(self, message):
        """
        adds the message to the next_message_sent_queue
        :param message:
        :return:
        """
        pass

    def _send_single_message(self):
        """
        sends a singles message over the socket
        :return:
        """
        pass

    def send_all(self):
        """
        sends all messages in next_message_sent_queue
        :return:
        """
        pass

    def _send_heartbeat(self):
        """
        sends a heartbeat messages and updates internal times
        :return:
        """
        pass

    def _got_heartbeat(self, heartbeat):
        """
        process a received heartbeat message
        :param heartbeat:
        :return:
        """
        pass

    def _heartbeat_check(self):
        """
        checks heartbeat and message timers
        compares them to current time and utility timeout
        if no heartbeat received connection is closed
        :return:
        """
        pass

    def _should_force_exit(self):
        """
        checks if exit command is timeing out
        :return: bool
        """
        pass

    def send_loop(self):
        """
        producer loop
        sends a single message at a time
        :return:
        """
        pass

    def receive_loop(self):
        """
        consumer loop
        processes a single message at a time
        :return:
        """
        pass

    def start_loop(self):
        """
        manager loop. Starts Producer/Consumer
        waits for new connection
        :return:
        """
        pass
