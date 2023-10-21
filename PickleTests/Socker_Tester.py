import PickleSocket
import time

pickle_server = PickleSocket.PickleSocket("TestServer", "127.0.0.1", 65432)
pickle_client = PickleSocket.PickleSocket("TestClient", "127.0.0.1", 65432)

pickle_server.start_manager(is_server=True)
pickle_client.start_manager()

for x in range(20):
    print(pickle_server.connection_status())
    print(pickle_client.connection_status())
    time.sleep(5)
