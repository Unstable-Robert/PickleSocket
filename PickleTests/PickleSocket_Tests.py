import unittest
import time
from unittest.mock import MagicMock, patch
from PickleSocket import PickleSocket, SocketStatus, MessageType, Message


class TestPickleSocket(unittest.TestCase):

    def setUp(self):
        self.pickle_server = PickleSocket("TestServer", "127.0.0.1", 12345)
        self.pickle_client = PickleSocket("TestClient", "127.0.0.1", 12345)
        time.sleep(20)

    def tearDown(self):
        self.pickle_client.manage_alive = False
        self.pickle_server.manage_alive = False

    @patch('socket.socket')
    def test_network_status(self, mock_socket):
        self.pickle_server.start_manager(is_server=True)
        self.pickle_client.start_manager(is_server=False)
        time.sleep(10)
        expected_status = f"Socket - 127.0.0.1:12345\nStatus: {SocketStatus.CONNECTED}\nConnected:True\n"
        self.assertEqual(first=self.pickle_server.connection_status(), second=expected_status)
        self.assertEqual(self.pickle_client.network_status, SocketStatus.CONNECTED)

    @patch('socket.socket')
    def test_connect_to_host(self, mock_socket):
        mock_socket.return_value = MagicMock()

        self.assertTrue(self.pickle_server._connect_to_host())
        self.assertEqual(self.pickle_server.network_status, SocketStatus.CONNECTED)

    def test_send_handshake_message(self):
        self.pickle_server.is_Server = False
        self.pickle_server._send_object = MagicMock()

        self.pickle_server._send_handshake_message()
        self.assertTrue(self.pickle_server.should_send_message)

    @patch('socket.socket')
    def test_proc_handshake_massage(self, mock_socket):
        handshake_message = Message(MessageType.INIT, 'key')
        self.pickle_server._get_object = MagicMock(return_value=handshake_message)
        self.assertTrue(self.pickle_server._proc_handshake_massage())
        self.assertTrue(self.pickle_server.connection_alive)

    def test_send_disconnect_message(self):
        self.pickle_server._send_object = MagicMock()
        self.pickle_server._should_force_exit = MagicMock(return_value=True)

        self.assertTrue(self.pickle_server.send_disconnect_message())
        self.assertFalse(self.pickle_server.connection_alive)

    @patch('socket.socket')
    def test_get_object(self, mock_socket):
        message = Message(MessageType.MSG, 'TestMessage')
        self.pickle_server.recv_data = message.encode()
        self.pickle_server.data = message.encode()

        result = self.pickle_server._get_object()

        self.assertEqual(result, message)

    def test_queue_next_message_send(self):
        message = Message(MessageType.MSG, 'TestMessage')
        self.assertTrue(self.pickle_server.queue_next_message_send(message))
        self.assertEqual(self.pickle_server.next_msg_sent.qsize(), 1)

    @patch('socket.socket')
    def test_send_all(self, mock_socket):
        message = Message(MessageType.MSG, 'TestMessage')
        self.pickle_server.queue_next_message_send(message)
        self.pickle_server._send_object = MagicMock()

        self.assertTrue(self.pickle_server.send_all())

    def test_send_heartbeat(self):
        self.pickle_server.queue_next_message_send = MagicMock()
        self.pickle_server._send_heartbeat()
        self.assertTrue(self.pickle_server.queue_next_message_send.called)


if __name__ == '__main__':
    unittest.main()
