##PickleSocket - Python Socket Library for Sending Python Objects

PickleSocket is an open-source Python library that simplifies sending Python objects over socket connections. It allows you to create and manage socket connections, send and receive Python objects, and handle various socket-related tasks. This library is designed for use in both client-server and peer-to-peer scenarios.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
  - [Initializing a PickleSocket](#initializing-a-picklesocket)
  - [Starting the PickleSocket](#starting-the-picklesocket)
  - [Sending Messages](#sending-messages)
  - [Receiving Messages](#receiving-messages)
  - [Ending Connections](#Ending Connections)
- [Message Types](#message-types)
- [Configuration](#configuration)
- [Contributing](#contributing)
- [License](#license)

## Installation

To use PickleSocket, simply download the `PickleSocket.py`, `PickMessage.py`, and `PickleUtility.py` files and include them in your project. Make sure you have Python installed on your system.

## Usage

### Initializing a PickleSocket

```python
from PickleSocket import PickleSocket

# Create a PickleSocket instance
# Parameters:
# name: Name of the network
# ip: IP address to bind/connect
# port: Port to use for the socket
# network_key: A shared key for secure communication (optional)
pickle_socket = PickleSocket("MyNetwork", "127.0.0.1", 8080, "my_secret_key")
```

### Starting the PickleSocket

You can start the PickleSocket as a server or client.

#### Starting as a Server

```python
# Start the PickleSocket as a server
pickle_socket.start_manager(is_server=True)
```

#### Starting as a Client

```python
# Start the PickleSocket as a client
pickle_socket.start_manager()
```

### Sending Messages

You can send various types of messages using PickleSocket. Messages are Python objects serialized and sent over the socket.

```python
# Sending a text message
pickle_socket.queue_next_message_send("Hello, PickleSocket!")

# Sending a custom message with MessageType
from PickleSocket import MessageType, Message
message = Message(MessageType.MOTOR, "Speed: 100 km/h")
pickle_socket.queue_next_message_send(message)
```

### Receiving Messages

You can receive messages in a separate thread. The received messages are stored in message queues for processing.

```python
# Access the last received message
last_received_message = pickle_socket.last_msg_recv.get()
```

Sure, here's the updated section titled "Ending Connections" in the README:

### Ending Connections

You can gracefully end connections by sending the disconnect message, and flush all remaining queued messages.

#### Sending Disconnect Messages

You can send a disconnect message to the other end, indicating your intention to end the connection.

```python
# Sending a disconnect message to the other end
pickle_socket.send_disconnect_message()
```

Remember to implement appropriate disconnection handling in your application based on your specific use case.

## Message Types

PickleSocket supports various message types defined in `PickMessage.py`. You can use these message types to categorize and process your messages. These include:

- `INIT`: Initial connection message
- `EXIT`: Disconnect message
- `HEART_BEAT`: Heartbeat message
- `SETTINGS`: Custom settings message
- `MSG`: Text message
- `IMAGE`: Image data
- `MOTOR`: Motor control data
- `GPS_DATA`: GPS data

## Configuration

You can configure various settings in `PickleUtility.py` to customize PickleSocket's behavior, including message send and receive delays, maximum message queue size, and socket timeouts.

## Contributing

If you'd like to contribute to PickleSocket, please feel free to fork the repository and submit pull requests. Your contributions are highly appreciated.

## License

PickleSocket is released under the [MIT License](LICENSE). You are free to use, modify, and distribute this library as per the terms of the license.
