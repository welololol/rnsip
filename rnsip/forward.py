import socket
import threading
import RNS
from const import *
from utility import *

class TCPPortForward:
    def __init__(self,settings, client, ):
        self.client = client
        self.remote_connection = settings.remote_connection
        self.local_connection = settings.local_connection
        threading.Thread(target=self.listener,args = (), daemon=False).start()

    def listener(self):
        with socket.socket() as listening_sock:
            ## allows for quick rebinding
            listening_sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1) 
            listening_sock.bind((self.local_connection.host.hostname, self.local_connection.port))
            listening_sock.listen()
            print(f"listening on {self.local_connection.host.hostname}:{self.local_connection.port}")
            while True:
                client_soc, client_address = listening_sock.accept()
                # Send each "client_soc" connection as a parameter to a thread.
                threading.Thread(target=self.connection, args=(client_soc,), daemon=True).start()         

    def connection(self, tcp_connection):
        # connection_type = ConnectionType(CMD_CONNECT, ATYP_DOMAINNAME , self.remote_connection)
        if hasattr(self.client, "client_link"):
        
            self.client.client_link.new_connection(tcp_connection, connection_type=self.remote_connection)
        else:
            print(f"attempted to make connection to {self.remote_connection} from {self.local_connection} but link has not been formed")
