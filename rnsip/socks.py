import RNS
import socket
import struct
import threading
from utility import *

class SocksProxyLocal:

    def __init__(self, option_settings, client):
        print("new local whateve")
        self.client = client
        self.option_settings = option_settings;
        self.socks_host = option_settings.socks_host
        print("yea")
        threading.Thread(target=self.listener,args = (), daemon=False).start()


    def listener(self):
        print("listening")
        with socket.socket() as listening_sock:
            print("idk")
            ## allows for quick rebinding
            listening_sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1) 
            RNS.log(f"listening on {str(self.socks_host.host)}:{self.socks_host.port}")
            listening_sock.bind((str(self.socks_host.host), self.socks_host.port))
            listening_sock.listen()
            while True:
                client_soc, client_address = listening_sock.accept()
                # Send each "client_soc" connection as a parameter to a thread.
                threading.Thread(target=self.connection, args=(client_soc, self.client), daemon=True).start()         
        
    def connection(self, con, client):
        # print(con, client)
        initial_request = struct.unpack("!BB",read_exact_from_socket(con,2));
        version = initial_request[0]
        hdr = initial_request[1];

        print(con)
        print(f"version:  {version}")

        # we do need this print btw.
        # 
        # print(con.recv(hdr), "hdr") # we ignore all methods for initiation cause we just accept it caues it's localhost
        methods = read_exact_from_socket(con,hdr)
        print("next", methods)

        con.sendall(bytes([0x05, 0x00])) ## version number + we don't auth you don't have to send anything

        print("sent")
        # after faking the auth process, we just start making a connection

        client.client_link.new_connection(con)
