from tracemalloc import DomainFilter
from asyncio.constants import ACCEPT_RETRY_DELAY
import threading
import RNS
import struct
import socket
import time
from utility import *
from RNS.vendor import umsgpack as msgpack
from const import * 

class Server: # only one instance of this exists

    def __init__(self, server):
        destination = RNS.Destination(server._identity_bytes, RNS.Destination.IN, RNS.Destination.SINGLE, "ip", "socksv5");
        destination.accepts_links(accepts=True)
        print(f"Destination: {RNS.prettyhexrep(destination.hash)}")

        destination.announce(app_data=b"blahblha" );
        destination.set_link_established_callback(self.new_connection);

    def new_connection(self, link):
        self.latest_server_link = ServerLink(self, link) # stupid variable

class ServerLink: # This is per client connection

    def __init__(self, server, link):
        self.server = server;
        self.link = link;
        self.buffers = {} ## int to connections;
        self.channel = link.get_channel();
        self.master_buffer = MasterBufferServer(self,self.channel); # not techincally the same thign but whatever


    def teardown_link(self):

        RNS.log("TEARING DOWN LINK")
        self.link.teardown();

    def new_connection(self, buffer_id):
        self.buffers[buffer_id] = Connection(buffer_id, self.channel) 

    def close_connection(self,id):
        pass
        


class Connection: ## an individual tcp or udp connection (not really udp but that'll be insideo f this)
    def __init__(self, buffer_id, channel):
        self.buffer = ReticulumBufferWrapper(channel, buffer_id);
        print(buffer_id, f"buffer start: {buffer_id}")
        connection_type = ConnectionType.read_buf(self.buffer.read_exact)
        print(buffer_id, f"buffer end: {buffer_id}")
        
        self.remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.remote_socket.connect((connection_type.host.hostname,connection_type.port))

        self.buffer.write(bytes([REP_SUCCEEDED]));

        BufferTcpExchange(self.buffer, self.remote_socket)
        


    def get_connection_type():
        pass

    def run_connect():
        pass

    def run_udp_associate():
        pass

    def run_bind():
        pass

class MasterBufferServer:

    def master_interaction_thread(self):
        buffer = self.buffer

        initial_request = struct.unpack("!BH", buffer.read_exact(3)) ## change later
        cmd = initial_request[0];
        if cmd != 0x01:
            self.server_link.teardown_link()

        password_len = initial_request[1]
        password_bytes = buffer.read_exact(password_len)

        announce_data = b"dada"[:65535] # make sure to limit max size;
        announce_len = len(announce_data)

        data = struct.pack("!BH",ACCEPT_AND_ANNC,announce_len)
        buffer.write(data);
        buffer.write(announce_data);

        while True:
            cmd = struct.unpack("!B", buffer.read_exact(1))[0];
            if cmd == 0x03:
                connection_id = struct.unpack("!I", buffer.read_exact(4))[0]; 
                print(f"new connection {connection_id}")
                threading.Thread(target=self.server_link.new_connection,args = (connection_id,), daemon=True).start();
            elif cmd == 0x04:
                connection_id = struct.unpack("!I", buffer.read_exact(4))[0]; 
                print(f"new connection2 {connection_id}")
                threading.Thread(target=self.server_link.end_connection,args = (connection_id,), daemon=True).start();
            else:
                pass


    def __init__(self, server_link ,channel):
        self.server_link = server_link
        self.buffer = ReticulumBufferWrapper(channel, 1)
        threading.Thread(target=self.master_interaction_thread,args = (), daemon=True).start();


