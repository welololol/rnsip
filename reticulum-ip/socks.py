import RNS
import socket
import struct
import threading

class SocksProxyServer:

    def __init__(self, client):
        self.client = client
        threading.Thread(target=self.listener,args = (), daemon=False).start()


    def listener(self):
        with socket.socket() as listening_sock:
            ## allows for quick rebinding
            listening_sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1) 
            listening_sock.bind(("127.0.0.1", 1080))
            listening_sock.listen()
            RNS.log(f"listening on localhost:{1080}")
            while True:
                client_soc, client_address = listening_sock.accept()
                # Send each "client_soc" connection as a parameter to a thread.
                threading.Thread(target=self.connection, args=(client_soc, self.client), daemon=True).start()         
        
    def connection(self, con, client):
        # print(con, client)
        initial_request = struct.unpack("!BB", con.recv(2));
        version = initial_request[0]
        hdr = initial_request[1];

        # we do need this print btw.
        # 
        # print(con.recv(hdr), "hdr") # we ignore all methods for initiation cause we just accept it caues it's localhost
        methods = con.recv(hdr)
        print("next", methods)

        con.sendall(bytes([0x05, 0x00])) ## version number + we don't auth you don't have to send anything

        print("sent")
        # after faking the auth process, we just start making a connection

        client.client_link.new_connection(con)

        return

        
        request_details = struct.unpack("!BBBB", con.recv(4)) ## reply on what the client what's to do
        version = request_details[0]
        cmd = request_details[1]
        # request_details[2] is rsv which is used by the spec
        atyp = request_details[3]

        if atyp == 0x01: ## ipv4 host
            host = socket.inet_ntoa(con.recv(4))
        elif atyp == 0x03: ## hostname host
            host_size = struct.unpack("!B",con.recv(1));
            data = con.recv(host_size[0])
            print(data)
            host = data.decode("utf-8");
        elif atyp == 0x04: # ipv6 host
            host = socket.inet_ntop(socket.AF_INET6, con.recv(16))

        port = struct.unpack("!H", con.recv(2))[0];

        con.sendall(bytes([0x05, 0x00, 0x00, 0x01, 0,0,0,0, 0,0]))
        # gives some bogus response equivalent to "yea we gonna sent all your traffic to 0.0.0.0:0,
        # don't worry about it the operation was successful. trust me bro

        print(host,port)

        while True:
            data = con.recv(455)
            print(data)


