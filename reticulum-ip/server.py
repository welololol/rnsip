import threading
import RNS
import struct
import socket
import time
from utility import ReticulumBufferWrapper
from RNS.vendor import umsgpack as msgpack
class Server: # only one instance of this exists

    def __init__(self, identity):
        destination = RNS.Destination(identity, RNS.Destination.IN, RNS.Destination.SINGLE, "ip", "socksv5");
        destination.accepts_links(accepts=True)

        destination.announce(app_data=b"blahblha" );

        print("socksv5 destination: " + RNS.prettyhexrep(destination.hash))

        print(threading.current_thread())
        destination.set_link_established_callback(self.new_connection);

    def new_connection(self, link):
        print("new link")
        print(threading.current_thread())
        self.latest_server_link = ServerLink(self, link) # stupid variable
        print("end final")

class ServerLink: # This is per client connection

    def __init__(self, server, link):
        self.server = server;
        self.link = link;
        self.buffers = {} ## int to connections;
        self.channel = link.get_channel();
        # print("buffer")
        # print(self.master_buffer)
        self.master_buffer = MasterBufferServer(self,self.channel); # not techincally the same thign but whatever

        # while True:
            # time.sleep(1)


    def teardown_link(self):

        RNS.log("TEARING DOWN LINK")
        self.link.teardown();

    def new_connection(self, buffer_id):
        return Connection(buffer_id, self.channel) 



    def tear_down_buffer(self,id):
        pass


class Connection: ## an individual tcp or udp connection (not really udp but that'll be insideo f this)
    def __init__(self, buffer_id, channel):
        self.buffer = ReticulumBufferWrapper(channel, buffer_id);


        # print(self.buffer.read(100))
        # print(self.buffer.read(100))
        # print(self.buffer.read(100))
        # print(self.buffer.read(100))
        # print(self.buffer.read(100))

        # return
        connection_response = struct.unpack("!BB",self.buffer.read_exact(2));
        cmd = connection_response[0]
        atyp = connection_response[1]

        if atyp == 0x03:
            host_size = struct.unpack("!B",self.buffer.read_exact(1))[0];
            data = self.buffer.read_exact(host_size)
            host = data.decode("utf-8");
            print(f"host: {host}")
        else:
            print(f"unsupported for rn!!!!!!!!!! {cmd}")

        port = struct.unpack("!H", self.buffer.read_exact(2))[0];
        print(f"port {port}")

        
        self.remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.remote_socket.connect((host,port))
        print("connected to remote")

        self.buffer.write(bytes([0x05]));
        print("sent back")

        threading.Thread(target=self.read_from_reticulum_side,args = (), daemon=True).start();
        threading.Thread(target=self.write_to_reticulum_side,args = (), daemon=True).start();
        

    def read_from_reticulum_side(self):
        while True:
            data = self.buffer.read(1000);
            print(f"receiving data {data}")
            try:
                self.remote_socket.sendall(data)
            except Exception:
                print("errored lol")

    def write_to_reticulum_side(self):
        while True:
            data = self.remote_socket.recv(1000);
            if len(data) > 0:
                print(f"sending data to reticulum {data} on {self.buffer.id}")
                self.buffer.write(data);
                print("finished sending")

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
        print(password_len)
        password_bytes = buffer.read_exact(password_len)

        print(password_bytes);

        announce_data = b"dada"[:65535] # make sure to limit max size;
        announce_len = len(announce_data)

        data = struct.pack("!BH",0x02,announce_len)
        buffer.write(data);
        buffer.write(announce_data);

        print("a")
        while True:
            RNS.log("more")
            cmd = struct.unpack("!B", buffer.read_exact(1))[0];
            if cmd == 0x03:
                connection_id = struct.unpack("!I", buffer.read_exact(4))[0]; 
                print("NEW CONNECTION", connection_id)
                threading.Thread(target=self.server_link.new_connection,args = (connection_id,), daemon=True).start();
                print("after")
                # thread.
                # self.server_link.new_connection(connection_id)
            elif cmd == 0x04:
                connection_id = struct.unpack("!I", buffer.read_exact(4))[0]; 
                threading.Thread(target=self.server_link.end_connection,args = (connection_id,), daemon=True).start();
                print("after")
                # self.server_link.end_connection(connection_id)
            else:
                RNS.log("invalid command on master " + str(cmd))
        print("end of the whatever")


    def __init__(self, server_link ,channel):

        print("buffer object")
        self.server_link = server_link
        # time.sleep(5.1)
        self.buffer = ReticulumBufferWrapper(channel, 1)
        # makes the callback a new thread so it doesn't block everything, at least I think, I'm bad at python threads
        # but not making a thread breaking everything so.
        threading.Thread(target=self.master_interaction_thread,args = (), daemon=True).start();

        # while True:
            # raw = buffer.read(1000)
            # time.sleep(1)
            # thread.
            # print(raw)

