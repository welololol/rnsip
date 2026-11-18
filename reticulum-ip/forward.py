import socket
import threading
import RNS
from const import *
from utility import *

class TCPPortForward:
    def __init__(self,client, remote_hostname,remote_port,local_hostname, local_port):
        self.remote_hostname = remote_hostname
        self.client = client
        self.remote_port = remote_port
        with socket.socket() as listening_sock:
            ## allows for quick rebinding
            listening_sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1) 
            listening_sock.bind((local_hostname, local_port))
            listening_sock.listen()
            RNS.log(f"listening on {local_hostname}:{local_port}")
            while True:
                client_soc, client_address = listening_sock.accept()
                # Send each "client_soc" connection as a parameter to a thread.
                threading.Thread(target=self.connection, args=(client_soc,), daemon=True).start()         

    def connection(self, tcp_connection):
        connection_type = ConnectionType(CMD_CONNECT, ATYP_DOMAINNAME , self.remote_hostname, self.remote_port)
        
        print("local connection made")
        self.client.client_link.new_connection(tcp_connection, connection_type=connection_type)
