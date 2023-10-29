# PickleSocket
Socket Library for maintaining connection between server and client. The current intented use is to keep a connection alive with a heartbeat set up. It's been developed using a raspberry pi 4 as the "server" and a desktop compter as the "client". The impltementation is meant to be used as a means of communication with robotics projects.

# Messages
The message are serailized using pickle library and than sent over the socket connection. This allows for easy interaction with python objects on the server and client.

# Server & Client
Both the server and client operate in a similair fasion. The differance being the server waits for a connection and will start the heartbeat message. The client initiatates the connection and will respond to heartbeats. Currenlty working like a game of marko pollo.
