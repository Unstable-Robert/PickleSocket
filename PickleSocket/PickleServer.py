import queue
import socket
import threading
import time
import logging
import struct
import pickle


class PickleServer:
    """
    Host server for clients to connect too
    Manages receiver and sending threads
    Server thread reconnects on failure
    """

    def __init__(self, name, ip, port, network_key="key"):

        self.network_status = SocketStatus.INIT

        self.network_name = name
        self.network_key = network_key

        self.network_ip = ip
        self.network_port = port

        self.network_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.network_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.time_last_hrb_sent = None
        self.time_last_msg_sent = None
        self.time_last_msg_recv = None

        self.last_msg_recv = self.queue.Queue()
        self.last_msg_sent = self.queue.Queue()

        self.next_msg_out = self.queue.Queue()

        self.manage_thread = threading.Thread(target=None, daemon=True)
        self.producer_thread = threading.Thread(target=None, daemon=True)
        self.consumer_thread = threading.Thread(target=None, daemon=True)

        self.connection_alive = False
        self.manage_alive = True

        # ToDo double check if this should be self or only in get_object
        self.recv_data = b""
        self.payload_size = struct.calcsize(">L")

        logger_name = self.network_name + __name__

    def connection_status(self):
        """
        Summary and current status of connection.
        :return: Formatted string with ip, port, connected, current state
        """
        s_status = f"Socket - {self.network_ip}:{self.network_port}\n" \
                   f"Status: {self.server_status}\n" \
                   f"Connected:{self.connection_alive}\n"
        return s_status

    def consumer_producer_init(self):
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

    def start_consumer_producer_pair(self):
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
                self.consumer_producer_init()
                self.network_status = SocketStatus.CONNECTED
                self.producer_thread.start()
                self.consumer_thread.start()
            except threading.ThreadError:
                pass

