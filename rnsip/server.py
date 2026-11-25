from tracemalloc import DomainFilter
from asyncio.constants import ACCEPT_RETRY_DELAY
import threading
import RNS
import struct
import socket
import time
import filtering
from utility import *
from RNS.vendor import umsgpack as msgpack
from const import * 

class Server: # only one instance of this exists
    def __init__(self, settings):
        self.settings = settings
        self.latest_link_id = 100000 # we start at a higher id just so that links look different than other ids, doesn't cost anything really
        # as we already putting everything in a dict anyways, so this is just arbitary.
        self.links = {}
        destination = RNS.Destination(settings._identity_bytes, RNS.Destination.IN, RNS.Destination.SINGLE, "ip", "socksv5");
        destination.accepts_links(accepts=True)
        self.destination = destination

        threading.Thread(target=self.announcement_loop,args = (), daemon=True).start();

        destination.set_link_established_callback(self.link_connection);
        print(f"Destination: {RNS.prettyhexrep(destination.hash)}")

    def announcement_loop(self):
        settings_bytes = self.settings.to_bytes()
        while True:
            self.destination.announce(app_data=settings_bytes);
            time.sleep(self.settings._announcement_rate * 60)

    def link_connection(self, link):
        # shouldn't link have their own id, can't find api for it?
        # not sure if we need a lock cause I don't think the callback makes a new thread, check later.
        id = self.latest_link_id + 1
        self.latest_link_id = id;
        print(f"new link of id {id}")
        server_link = ServerLink(self, link, id)
        self.links[id] = server_link 
        print(f"new link of id {id}")

        def on_close(link):
            print(f"link of id {id} has been closed")
            print(server_link)
            server_link.teardown()

        link.set_link_closed_callback(on_close)


class ServerLink: # This is the per client/link connection

    def __init__(self, server, link, link_id):
        self.server = server;
        self.link = link;
        self.link_id = link_id
        self.connections = {} ## int to connections but we actually use a directory
        self.channel = link.get_channel();
        self.adding_connections_lock = threading.Lock();
        print("creating buffer")
        self.master_buffer = MasterBufferServer(self,self.channel); # not techincally the same thign but whatever
        self.buffer_of_connections(2)
        print("end")



    def teardown(self):
        RNS.log("TEARING DOWN LINK (kill all connections?)")

        self.link.teardown();
        print(self.connections)
        for connection in self.connections.values():
            connection.teardown(internal=False)

    def buffer_of_connections(self, latest_buffer_id):
        self.adding_connections_lock.acquire()
        for id in range(latest_buffer_id,latest_buffer_id + DEFAULT_CONNECTION_BUFFER):
            if self.connections.get(id) == None:
                self.connections[id] = Connection(self, id) 
        self.adding_connections_lock.release()

    def close_connection_remote(self, id):
        self.master_buffer.close_connection_signal(id);

    def close_connection_local(self,id):
        self.connections[id].teardown(internal=False)
        del self.connections[id] # allows the underlying connection to be garbage collected

        


class Connection: ## an individual tcp or udp connection (not really udp but that'll be insideo f this)
    def __init__(self, server_link, buffer_id ):
        self.buffer = ReticulumBufferWrapper(server_link.channel, buffer_id);
        self.server_link = server_link
        self.finished_handshake = False;
        self.torndown = False;
        self.remote_socket = None;
        self.handshake_thread = threading.Thread(target=self.handshake,args = (), daemon=True).start();
        
    def handshake(self):
        connection_type = ConnectionType.read_buf(self.buffer.read_exact)
        self.server_link.buffer_of_connections(self.buffer.id)
        print(f"[{self.server_link.link_id}] [{self.buffer.id}] from request connection has been formed to {str(connection_type)}")
        new_address, connection_speed = filtering.filter_ip_based_on_settings(connection_type, self.server_link.server.settings)
        if self.torndown:
            return
        if new_address != None:
            self.buffer.write(bytes([REP_SUCCEEDED]));
            if self.torndown:
                return
            connection_type.host.hostname = new_address
            print(new_address, connection_speed)
            if connection_type.type == CMD_CONNECT:
                self.run_connect(connection_type) 
            else:
                print(f"invalid cmd for handshake {connection_type.type}")
        else:
            self.buffer.write(bytes([REP_FAILURE]));


    def teardown(self, internal=True):
        # if internal then propagate upwards to clientlink so that the other side knows, if not just delete
        print(f"[{self.server_link.link_id}] [{self.buffer.id}] is being torn-down {internal}")
        if self.finished_handshake:
            self.buffer_exchange.teardown_socket()
        else:
            ## must be paused on handshake
            if self.remote_socket: # assuming we ever even started the socket
                self.remote_socket.close()
        if internal == True:
            self.server_link.close_connection_remote(self.buffer_exchange.wrapped_buffer.id)
        self.torndown = True;


    def get_connection_type():
        pass

    def run_connect(self, connection_type):
        self.remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.remote_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        self.remote_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        # self.remote_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 30)
        self.remote_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4096)
        self.remote_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 4096)

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.remote_socket.connect((connection_type.host.hostname,connection_type.port))

        if self.torndown:
            return

        self.finished_handshake = True;

        self.buffer_exchange = BufferTcpExchange(self.buffer, self.remote_socket, self.teardown)

    def run_udp_associate():
        pass

    def run_bind():
        pass

class MasterBufferServer:

    def master_interaction_thread(self):
        buffer = self.buffer

        print(0)
        initial_request = struct.unpack("!BH", buffer.read_exact(3)) ## change later
        cmd = initial_request[0];
        print(f"cmd {cmd}")
        if cmd != 0x01:
            print(f" client send invalid command {cmd}")
            self.server_link.teardown_link()

        print(1)
        password_len = initial_request[1]
        password_bytes = buffer.read_exact(password_len)
        print(2)

        announce_data = b"dada"[:65535] # make sure to limit max size;
        announce_len = len(announce_data)

        data = struct.pack("!BH",ACCEPT_AND_ANNC,announce_len)
        buffer.write(data);
        buffer.write(announce_data);
        print("end of buffer")

        while True:
            cmd = struct.unpack("!B", buffer.read_exact(1))[0];
            print(f"cmd {cmd}")
            if cmd == END_CONNECTION:
                connection_id = struct.unpack("!I", buffer.read_exact(4))[0]; 
                threading.Thread(target=self.server_link.close_connection_local,args = (connection_id,), daemon=True).start();
            else:
                pass

    def __init__(self, server_link ,channel):
        self.server_link = server_link
        print("a")
        self.buffer = ReticulumBufferWrapper(channel, 1)
        print("b")
        threading.Thread(target=self.master_interaction_thread,args = (), daemon=True).start();

    def close_connection_signal(self, id):
        new_connection = struct.pack("!BI", END_CONNECTION, id); 
        print(new_connection)
        self.buffer.write(new_connection)
