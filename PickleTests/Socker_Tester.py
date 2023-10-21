import PickleSocket
import time

pickle_server = PickleSocket.PickleSocket("TestServer", "192.168.1.110", 65432)
pickle_client = PickleSocket.PickleSocket("TestClient", "localhost", 65432)

pickle_server.start_manager(is_server=True)
time.sleep(2)
pickle_client.start_manager()

for x in range(20):
    print(pickle_server.connection_status())
    print(pickle_client.connection_status())
    time.sleep(5)
