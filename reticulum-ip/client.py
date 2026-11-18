import RNS
import time
import threading
import struct
import socket
from utility import ReticulumBufferWrapper

class Client:
    def __init__(self, destination):
        RNS.Link(destination, established_callback=self.new_link)

    def new_link(self, link):
        print("Link made with the server")
        self.client_link = ClientLink(link)


class ClientLink:
    def __init__(self, link):
        self.id_rolling = 1;
        self.link = link
        self.buffers = {}
        self.channel = link.get_channel();
        print("buffer")
        self.master_buffer = MasterBufferClient(self, self.channel)

    def new_connection(self, tcp_socket_connection):
        self.id_rolling += 1
        self.master_buffer.new_connection(self.id_rolling);

        buffer = ReticulumBufferWrapper(self.channel, self.id_rolling)
        print(f"new connection i guess with id {self.id_rolling}")
        self.buffers[self.id_rolling] = SocksClientConnection(tcp_socket_connection, buffer)
        

class MasterBufferClient:

    def master_interaction_thread(self):
        self.buffer.write(bytes([0x01,0x00,0x00])); ## should be a password thing here later. But this is basically saying no pass


        a = self.buffer.read(3)
        print(a)
        announce_cmd_return = struct.unpack("!BH",a);
        cmd = announce_cmd_return[0]
        if cmd != 0x02:
            print("ERROR")

        announce_len  = announce_cmd_return[1]
        print(announce_len)
        announce_data = self.buffer.read(announce_len)

        # by this point, the connection has be initialised.
        # the only thing the client needs to listen for is the server tearing down a connection
        # the only thing the server is listening for, is the client creating connections and also tearing them down
        # these are independant in the sense that we aren't looking for a reply, because the reply is sent in a different
        # buffer than the master one. So while possibly confusing, we don't have any syncing queue here, we just send
        # requests directly and assume that it'll be fine.
        
        # BUT, we need a loop to receive server data (for the tearing down of connections if the server does that)

        print("master buffer on standby mode")
        while True:
            cmd_return = struct.unpack("!B",self.buffer.read_exact(1));
            cmd = announce_cmd_return[0]
            print("received command from server:", cmd)


    def __init__(self, client_link , channel):
        self.buffer = ReticulumBufferWrapper(channel, 1)

        threading.Thread(target=self.master_interaction_thread,args = (), daemon=True).start();

    def new_connection(self, id):
        new_connection = struct.pack("!BI", 0x03, id); 
        self.buffer.write(new_connection)


class SocksClientConnection:

    def read_from_reticulum_side(self):
        while True:
            data = self.buffer.read(1000);
            print(f"receiving data {data}")
            try:
                self.tcp_socket.sendall(data)
            except Exception:
                print("errored lol")

    def write_to_reticulum_side(self):
        while True:
            data = self.tcp_socket.recv(1000);
            if len(data) > 0:
                print(f"sending data to reticulum {data} on {self.buffer.id}")
                self.buffer.write(data);
                print("finished sending")

    def handshake(self):
        request_details = struct.unpack("!BBBB", self.tcp_socket.recv(4)) ## reply on what the client what's to do
        version = request_details[0]
        cmd = request_details[1]
        # request_details[2] is rsv which isn't used by the spec
        atyp = request_details[3]

        if atyp == 0x01: ## ipv4 host
            host = socket.inet_ntoa(self.tcp_socket.recv(4))
        elif atyp == 0x03: ## hostname host
            host_size = struct.unpack("!B",self.tcp_socket.recv(1))[0];
            data = self.tcp_socket.recv(host_size)
            print(data)
            host = data.decode("utf-8");
        elif atyp == 0x04: # ipv6 host
            host = socket.inet_ntop(socket.AF_INET6, self.tcp_socket.recv(16))

        port = struct.unpack("!H", self.tcp_socket.recv(2))[0];


        print("client side", host, port)
        print(f"command {cmd} {atyp}")
        if cmd == 0x01:
            pass

        ## this is for connect
        # 
        ## We only bother sending the cmd, atyp and the host 
        # to save on some bytes

        self.buffer.write(struct.pack("!BB",cmd,atyp))
        if atyp == 0x03:
            self.buffer.write(struct.pack("!B",host_size))
            self.buffer.write(host.encode("utf-8"))
        else:
            print("unsupported for rn!!!!!!!!!!")

        self.buffer.write(struct.pack("!H",port))

        # the server then only replies with if the command is succesful given by the standard
        # however it doesn't reply with the destination port or whatever cause it's irrevalant for the most part
        # so we instead just fake it back to the client

        server_response = struct.unpack("!B", self.buffer.read_exact(1))
        print(f"server response {server_response}")

        self.tcp_socket.sendall(bytes([0x05, 0x00, 0x00, 0x01, 0,0,0,0, 0,0]))
        # gives some bogus response equivalent to "yea we gonna sent all your traffic to 0.0.0.0:0,
        # don't worry about it the operation was successful. trust me bro.

        print(host,port)
        threading.Thread(target=self.read_from_reticulum_side,args = (), daemon=True).start();
        threading.Thread(target=self.write_to_reticulum_side,args = (), daemon=True).start();

    def flush_initial(self):
        # occasionally we will send data to the remote buffer
        # before it has actually initialised, which causes problems
        # so we just keep flushing the bytes till it works out
        for i in range(1,25):
            # pass
            time.sleep(0.01)
            self.buffer.flush();


    
    def __init__(self,tcp_socket, buffer):
        self.buffer = buffer;
        self.tcp_socket = tcp_socket

        threading.Thread(target=self.flush_initial,args = (), daemon=True).start();
        threading.Thread(target=self.handshake,args = (), daemon=True).start();

        # while True:
        #     new_data = tcp_socket_connection.recv(456);
        #     print("new data")
        #     print(new_data)
        #     buffer.write(new_data);

        #     sending_data = buffer.read(1200);
        #     print("new data 2")
        #     print(sending_data)
        #     tcp_socket_connection.sendall(sending_data)

