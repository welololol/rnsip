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
    def __init__(self, settings):
        self.settings = settings
        destination = RNS.Destination(settings._identity_bytes, RNS.Destination.IN, RNS.Destination.SINGLE, "ip", "socksv5");
        destination.accepts_links(accepts=True)
        self.destination = destination

        threading.Thread(target=self.announcement_loop,args = (), daemon=True).start();

        destination.set_link_established_callback(self.new_connection);
        print(f"Destination: {RNS.prettyhexrep(destination.hash)}")

    def announcement_loop(self):
        settings_bytes = self.settings.to_bytes()
        while True:
            self.destination.announce(app_data=settings_bytes);
            time.sleep(self.settings._announcement_rate * 60)

    def new_connection(self, link):
        print("New link")
        self.latest_server_link = ServerLink(self, link) 

class ServerLink: # This is the per client connection

    def __init__(self, server, link):
        self.server = server;
        self.link = link;
        self.connections = {} ## int to connections but we actually use a directory
        self.channel = link.get_channel();
        self.adding_connections_lock = threading.Lock();
        self.master_buffer = MasterBufferServer(self,self.channel); # not techincally the same thign but whatever

        self.buffer_of_connections(2)


    def teardown_link(self):
        RNS.log("TEARING DOWN LINK")

        self.link.teardown();

    def buffer_of_connections(self, latest_buffer_id):
        self.adding_connections_lock.acquire()
        for i in range(latest_buffer_id,latest_buffer_id + DEFAULT_CONNECTION_BUFFER):
            if self.connections.get(str(i)) == None:
                self.connections[str(i)] = Connection(self, i) 
        self.adding_connections_lock.release()

    def close_connection_remote(self, id):
        self.master_buffer.close_connection_signal(id);

    def close_connection_local(self,id):
        self.connections[str(id)].teardown()

        


class Connection: ## an individual tcp or udp connection (not really udp but that'll be insideo f this)
    def __init__(self, server_link, buffer_id ):
        self.buffer = ReticulumBufferWrapper(server_link.channel, buffer_id);
        self.server_link = server_link
        self.finished_handshake = True;
        self.handshake_thread = threading.Thread(target=self.handshake,args = (buffer_id,), daemon=True).start();
        
    def handshake(self, buffer_id):
        connection_type = ConnectionType.read_buf(self.buffer.read_exact)
        
        self.server_link.buffer_of_connections(buffer_id)

        self.remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.remote_socket.connect((connection_type.host.hostname,connection_type.port))
        self.buffer.write(bytes([REP_SUCCEEDED]));

        self.finished_handshake = True;
        def remote_close(exchange):
            self.server_link.close_connection_remote(exchange.wrapped_buffer.id)
            pass

        self.buffer_exchange = BufferTcpExchange(self.buffer, self.remote_socket, remote_close)

    def teardown(self):
        if self.finished_handshake:
            self.buffer_exchange.teardown_socket()
        else:
            ## must be paused on handshake
            self.remote_socket.close()
        
        # if  f

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
            if cmd == END_CONNECTION:
                connection_id = struct.unpack("!I", buffer.read_exact(4))[0]; 
                threading.Thread(target=self.server_link.close_connection_local,args = (connection_id,), daemon=True).start();
            else:
                pass

    def __init__(self, server_link ,channel):
        self.server_link = server_link
        self.buffer = ReticulumBufferWrapper(channel, 1)
        threading.Thread(target=self.master_interaction_thread,args = (), daemon=True).start();

    def close_connection_signal(self, id):
        new_connection = struct.pack("!BI", END_CONNECTION, id); 
        self.buffer.write(new_connection)
        self.buffer.flush()
