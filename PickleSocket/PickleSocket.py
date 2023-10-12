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


class PickleSocket:
    """
    Manage a socket connection that
    Sends python objects over socket
    """

    def __init__(self, name, ip, port, network_key="key"):

        self.network_status = SocketStatus.INIT

        self.util = Utility()

        self.is_Server = None

        self.network_name = name
        self.network_key = network_key

        self.network_ip = ip
        self.network_port = port

        self.network_client = None
        self.current_client_address = None

        logger_name = self.network_name + __name__

        self.logger = logging.getLogger(logger_name)

        if not self.logger.hasHandlers():
            console_handler, file_handler = self.util.set_up_logger_outputs(logger_name + ".log")

            self.logger.addHandler(console_handler)
            self.logger.addHandler(file_handler)

        self.logger.setLevel(self.util.get_log_level())

        self.network_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.network_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.network_socket.settimeout(self.util.SOCKET_LISTEN_TIMEOUT)

        self.time_last_hrb_recv = None
        self.time_last_hrb_sent = None

        self.time_last_msg_recv = None
        self.time_last_msg_sent = None


        self.time_exit_triggered = None

        self.last_msg_recv = None
        self.last_msg_sent = None
        self.next_msg_sent = None

        self._message_queue_init()

        self.manage_thread = threading.Thread(target=self.start_loop, daemon=True)
        self.producer_thread = threading.Thread(target=self.send_loop, daemon=True)
        self.consumer_thread = threading.Thread(target=self.receive_loop, daemon=True)

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

    def _message_queue_init(self):
        """
        sets up message queues
        :return:
        """
        self.last_msg_recv = queue.Queue()
        self.last_msg_sent = queue.Queue()

        self.next_msg_sent = queue.Queue()

    def _message_timers_init_current_time(self):
        """
        sets up message timers to current time
        :return:
        """
        self.time_since_last_heartbeat_sent = self.util.get_current_time()
        self.time_since_last_msg_sent = self.util.get_current_time()
        self.time_since_last_msg_received = self.util.get_current_time()

    def start_manager(self, is_server=False):
        """
        Start the manage thread to wait for a connection
        """
        try:
            if not self.manage_thread.isAlive():
                self.is_Server = is_server
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
        if not to_test.empty():
            if to_test.qsize() > self.util.MESSAGE_QUEUE_MAX_SIZE:
                return True
        return False

    def _queue_last_msg_recv(self, message):
        """
        queue message to last_msg_recv
        :param message:
        :return:
        """
        if self._should_reset_queue(self.last_msg_recv):
            self.logger.debug("Queue too big check it out")
            self.last_received = queue.Queue()

        self.last_msg_recv.put(message)

    def _queue_last_msg_sent(self, message):
        """
        queue message to last_msg_sent
        :param message:
        :return:
        """
        if self._should_reset_queue(self.last_msg_sent):
            self.logger.debug("Queue too big check it out")
            self.last_received = queue.Queue()

        self.last_msg_sent.put(message)

    def _queue_next_msg_sent(self, message):
        """
        queue message to next next_msg_sent
        :param message:
        :return:
        """
        if self._should_reset_queue(self.next_msg_sent):
            self.logger.debug("Queue too big check it out")
            self.last_received = queue.Queue()

        self.next_msg_sent.put(message)

    def reconnect(self):
        """
        tries to reconnect
        :return:
        """
        if self.is_Server:
            self._wait_for_client()
        else:
            self._connect_to_host()

    def _wait_for_client(self):
        """
        Waits for one socket timeout
        :return: bool on connection success
        """
        try:
            if self.network_status <= SocketStatus.INIT:
                self.network_socket.bind((self.network_ip, self.network_port))

            self._message_queue_init()

            self.time_exit_triggered = None
            self.logger.info(f"Listening on {self.network_ip}:{self.network_port}")

            self.network_socket.listen(self.util.NUMBER_ALLOWED_CONNECTIONS)
            self.network_client, self.current_client_address = self.network_socket.accept()
            self.network_socket.settimeout(self.util.SOCKET_CONNECTED_TIMEOUT)
            self.logger.info(f"Got connection from {self.current_client_address}")
            self._message_timers_init_current_time()
            return True
        except socket.error:
            self.logger.error(f"Socket Error - network_status:{self.network_status.name}")
            time.sleep(self.util.SERVER_WAIT_FOR_CONNECTION_DELAY)
        return False

    def _connect_to_host(self):
        """
        Waits for one socket timeout
        :return: bool on connection success
        """
        try:
            self._message_queue_init()
            self.time_exit_triggered = None
            self.logger.info(f"Connecting to {self.network_ip}:{self.network_port}")
            self.network_socket.connect((self.network_ip, self.network_port))
            return self._send_handshake_message()
        except socket.error:
            self.logger.error(f"Failed during socket connection [can't connect to host]")
        return False

    def _send_handshake_message(self):
        """
        client sends initial handshake message
        sends message with network key
        :return:
        """
        if not self.is_Server:
            key_message = Message(MessageType(MessageType.INIT.value), self.network_key)
            self.logger.debug(f"Key length: {key_message.size}")
            self._send_object(key_message)

            handshake_count = 0

            # ToDo set up way to wait for response
            while not self._proc_handshake_massage():
                if handshake_count > self.util.MAX_HANDSHAKE_COUNT:
                    self.logger.error("Handshake failed")
                    return False
                else:
                    handshake_count += 1
            self.should_send_message = True

    def _proc_handshake_massage(self):
        """
        server waits for handshake message
        sent on successfully connect by client
        """
        try:
            handshake_tmp = self._get_object()

            if not handshake_tmp:
                self.logger.error("No message received for handshake")
                return False
            if self.is_Server and self.network_key == handshake_tmp.contents:
                success_message = Message(MessageType(MessageType.INIT), "TRUE")
                self._send_object(success_message)
                self.connection_alive = True
                self.logger.debug(f"Handshake complete for is_Server: {self.is_Server}")
                return True
            if not self.is_Server and handshake_tmp.contents == "TRUE":
                self.connection_alive = True
                self.logger.debug(f"Handshake complete for is_Server: {self.is_Server}")
                return True
        except socket.error:
            self.logger.error("got socket error during handshake")
        except ValueError:
            self.logger.error("got value error during handshake")
        return False

    def send_disconnect_message(self):
        """
        sends disconnect message to client
        waits
        :return:
        """
        try:
            if self._should_force_exit():
                self.connection_alive = False
                self.logger.error("Force Closing Connection")
            else:
                self.logger.debug(f"Sending exit message is_Server: {self.is_Server}")
                close_message = Message(MessageType(MessageType.EXIT), self.network_key)
                self.queue_next_message_send(close_message)
                if not self.time_exit_triggered:
                    self.time_exit_triggered = self.util.get_current_time()
        except socket.error:
            try:
                self.logger.error(f"Failed to close connection {self.current_client_address}")
            except ValueError:
                self.logger.error(f"Disconnect triggered with no active connection")
        return False

    def _proc_disconnect_message(self, message):
        """
        handles closing the connection at the clients request
        :return:
        """
        close_message = Message(MessageType(MessageType.EXIT), self.network_key)
        self.queue_next_message_send(close_message)
        self.send_all()
        self.connection_alive = False
        self.time_exit_triggered = None
        # ToDo handle cleaning up remote closing connection
        self.logger.info("Got close connection command")

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
        try:
            if isinstance(message, str):
                self._queue_next_msg_sent(Message(MessageType(MessageType.MSG), message))
                return True
            elif isinstance(message, Message):
                self._queue_next_msg_sent(message)
                return True
            # elif isinstance(message, Setting):
            #     self._queue_next_msg_sent(message)
            #     return True
            else:
                self.logger.debug(f"Send message did not get a string: {type(message)}")
                return False
        except socket.error:
            self.logger.error("Socket error when sending message")
        except IndexError:
            self.logger.error("Index error when adding message to queue")
        except ValueError:
            self.logger.error("Value error when sending message")
        return False

    def _send_single_message(self):
        """
        sends a singles message over the socket
        :return:
        """
        try:
            if not self.next_msg_sent.empty():
                message = self.next_msg_sent.get(block=False)
                self.logger.debug(f"last_received count {self.next_msg_sent.qsize()}")
                if message:
                    self.logger.debug(f"sending message {message.contents}")
                    self._send_object(message)
        except TypeError:
            self.logger.error("Type error when sending message")
        except IndexError:
            self.logger.error("Index error when sending message")

    def send_all(self):
        """
        sends all messages in next_message_sent_queue
        :return:
        """
        try:
            if not self.next_msg_sent.empty():
                self.logger.info("Flushing all messages")
                while not self.next_msg_sent.empty():
                    message = self.next_msg_sent.get(block=False)
                    if message:
                        self._send_object(message)
                return True
        except ValueError:
            self.logger.error("value error when sending all messages")
        except IndexError:
            self.logger.error("index error when sending all")
        return False

    def _send_heartbeat(self):
        """
        sends a heartbeat messages and updates internal times
        :return:
        """
        try:
            new_heartbeat = Message(MessageType(MessageType.HEART_BEAT), str(self.util.get_current_time()))
            self.queue_next_message_send(new_heartbeat)
            self.logger.debug("Heartbeat added to queue....")
            return True
        except ValueError:
            self.logger.error("Value error when sending heartbeat")
        except socket.error:
            self.logger.error("Failed to send heartbeat socket")
        return False

    def _got_heartbeat(self, heartbeat):
        """
        process a received heartbeat message
        :param heartbeat:
        :return:
        """
        if self.is_Server:
            self.time_last_hrb_recv = self.util.get_current_time()
            self.logger.debug("Got heartbeat..updated time")
            return True
        else:
            self._send_heartbeat()
            self.time_last_hrb_sent = self.util.get_current_time()
            self.logger.debug("Got heartbeat..updated time")

    def _heartbeat_check(self):
        """
        checks heartbeat and message timers
        compares them to current time and utility timeout
        if no heartbeat received connection is closed
        :return:
        """
        try:
            if (self.util.get_current_time() - self.time_since_last_heartbeat_sent).total_seconds() > \
                    self.util.HEARTBEAT_DELAY * 3:
                if (
                        self.util.get_current_time() - self.time_since_last_msg_received).total_seconds() > \
                        self.util.HEARTBEAT_OVERRIDE * 3:
                    self.logger.error("failed to get heartbeat in 3 tries..closing connection")
                    self.send_disconnect_message()
                return False
            elif (self.util.get_current_time() - self.time_since_last_heartbeat_sent).total_seconds() > \
                    self.util.HEARTBEAT_DELAY or \
                    (self.util.get_current_time() - self.time_since_last_msg_received).total_seconds() > \
                    self.util.HEARTBEAT_OVERRIDE or \
                    (self.util.get_current_time() - self.time_since_last_msg_sent).total_seconds() > \
                    self.util.HEARTBEAT_OVERRIDE:
                self.logger.debug("Should send heartbeat....")
                self._send_heartbeat()
                # ToDo add fix so a million heartbeats arent added when connection is lost
                return True
        except socket.error:
            self.logger.error("Socket error in heartbeat check")
        return False

    def _should_force_exit(self):
        """
        checks if exit command is timeing out
        :return: bool
        """
        if self.time_exit_triggered:
            if (self.util.get_current_time() - self.time_exit_triggered).total_seconds() > self.util.HEARTBEAT_DELAY * 4:
                return True
            else:
                return False

    def send_loop(self):
        """
        producer loop
        sends a single message at a time
        :return:
        """
        while self.connection_alive:
            self._send_single_message()
            time.sleep(self.util.MESSAGE_SEND_DELAY)
        self.logger.error("Send loop ended.....")

    def receive_loop(self):
        """
        consumer loop
        processes a single message at a time
        :return:
        """
        while self.connection_alive:
            message = self._get_object()

            if message:
                if message.type == MessageType.EXIT:
                    self._proc_disconnect_message(message)
                elif message.type == MessageType.SETTINGS:
                    # ToDo handle settings message
                    self.logger.info(f"Got settings message {message.contents}")
                    self._queue_last_msg_recv(message)
                else:
                    self._queue_last_msg_recv(message)
                self.logger.debug(f"last_received count {self.last_msg_recv.qsize()}")
            time.sleep(self.util.MESSAGE_RECEIVE_DELAY)
        self.logger.error("receive loop ended.....")

    def start_loop(self):
        """
        manager loop. Starts Producer/Consumer
        waits for new connection
        :return:
        """
        while self.manage_alive:
            self.network_status = SocketStatus.WAITING_FOR_CONNECTION
            # Waiting for connection stage
            if not self.connection_alive:
                self.network_status = SocketStatus.WAITING_FOR_CONNECTION
                self.logger.debug("server thread alive")
                if self.is_Server:
                    got_connection = self._wait_for_client()
                else:
                    got_connection = self._connect_to_host()

                if got_connection:
                    if self._proc_handshake_massage():
                        self.connection_alive = True
                        self._start_consumer_producer_pair()
                    else:
                        self.logger.error("Connection handshake failed")
                else:
                    self.logger.debug("resting")
                    time.sleep(self.util.SERVER_WAIT_FOR_CONNECTION_DELAY)
            else:
                if self.connection_alive:
                    if not self._heartbeat_check():
                        self.logger.debug("waiting to send heartbeat")
                time.sleep(self.util.SERVER_WAIT_FOR_CONNECTION_DELAY)
