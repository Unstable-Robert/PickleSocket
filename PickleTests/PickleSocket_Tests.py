import unittest
from unittest.mock import MagicMock, patch
from PickleSocket import PickleSocket, SocketStatus, MessageType, Message


class TestPickleSocket(unittest.TestCase):

    def setUp(self):
        self.pickle_socket = PickleSocket("TestSocket", "127.0.0.1", 12345)

    def tearDown(self):
        self.pickle_socket.manage_alive = False

    def test_connection_status(self):
        expected_status = f"Socket - 127.0.0.1:12345\nStatus: {SocketStatus.INIT}\nConnected:False\n"
        self.assertEqual(self.pickle_socket.connection_status(), expected_status)

    @patch('socket.socket')
    def test_wait_for_client(self, mock_socket):
        self.pickle_socket.is_Server = True
        mock_socket.return_value = MagicMock()
        mock_socket.return_value.accept.return_value = (MagicMock(), 'client_address')

        self.assertTrue(self.pickle_socket._wait_for_client())
        self.assertEqual(self.pickle_socket.network_status, SocketStatus.CONNECTED)

    @patch('socket.socket')
    def test_connect_to_host(self, mock_socket):
        mock_socket.return_value = MagicMock()

        self.assertTrue(self.pickle_socket._connect_to_host())
        self.assertEqual(self.pickle_socket.network_status, SocketStatus.CONNECTED)

    def test_send_handshake_message(self):
        self.pickle_socket.is_Server = False
        self.pickle_socket._send_object = MagicMock()

        self.pickle_socket._send_handshake_message()
        self.assertTrue(self.pickle_socket.should_send_message)

    @patch('socket.socket')
    def test_proc_handshake_massage(self, mock_socket):
        handshake_message = Message(MessageType.INIT, 'key')
        self.pickle_socket._get_object = MagicMock(return_value=handshake_message)
        self.assertTrue(self.pickle_socket._proc_handshake_massage())
        self.assertTrue(self.pickle_socket.connection_alive)

    def test_send_disconnect_message(self):
        self.pickle_socket._send_object = MagicMock()
        self.pickle_socket._should_force_exit = MagicMock(return_value=True)

        self.assertTrue(self.pickle_socket.send_disconnect_message())
        self.assertFalse(self.pickle_socket.connection_alive)

    @patch('socket.socket')
    def test_get_object(self, mock_socket):
        message = Message(MessageType.MSG, 'TestMessage')
        self.pickle_socket.recv_data = message.encode()
        self.pickle_socket.data = message.encode()

        result = self.pickle_socket._get_object()

        self.assertEqual(result, message)

    def test_queue_next_message_send(self):
        message = Message(MessageType.MSG, 'TestMessage')
        self.assertTrue(self.pickle_socket.queue_next_message_send(message))
        self.assertEqual(self.pickle_socket.next_msg_sent.qsize(), 1)

    @patch('socket.socket')
    def test_send_all(self, mock_socket):
        message = Message(MessageType.MSG, 'TestMessage')
        self.pickle_socket.queue_next_message_send(message)
        self.pickle_socket._send_object = MagicMock()

        self.assertTrue(self.pickle_socket.send_all())

    def test_send_heartbeat(self):
        self.pickle_socket.queue_next_message_send = MagicMock()
        self.pickle_socket._send_heartbeat()
        self.assertTrue(self.pickle_socket.queue_next_message_send.called)


if __name__ == '__main__':
    unittest.main()
