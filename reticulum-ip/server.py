import threading
import RNS
import struct
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
        self.master_buffer2 = MasterBufferServer(self,self.channel); # not techincally the same thign but whatever

        # while True:
            # time.sleep(1)



    def teardown_link(self):
        self.link.teardown();

    def new_connection(self, buffer_id):
        print("new connection")
        buffer = RNS.Buffer.create_bidirectional_buffer(buffer_id,buffer_id, self.channel);

        # make it so this creating a new thread that listens on this buffer
        # when buffer completes and get's the type and hostname+port of the connection, return
        # to this thread, then makes another class that does that.
        
         # so in the array/hash of bufers, it's first the "handshake" class that figures out what is going on
         # then it is replaced by the type of connection it is.
        return Connection(buffer) 



    def tear_down_buffer(self,id):
        pass


class Connection: ## an individual tcp or udp connection (not really udp but that'll be insideo f this)
    def __init__(self, buffer):
        print("new buffer")
        while True:
            print(buffer.read(455))

        pass


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

        # cmd = struct.unpack("!B", buffer.read_exact(1)) ## change later
        # if cmd != 0x01:
        #     self.server_link.teardown_link()

        # print("a")
        # announce_data = b"dada"[:65535] # make sure to limit max size;
        # announce_len = len(announce_data)

        # data = struct.pack("!BH",0x01,announce_len)
        # buffer.write(data);
        # print("okay")
        # buffer.write(announce_data);
        # print("a")

        while True:
            RNS.log("more")
            # cmd = struct.unpack("!B", buffer.read_exact(1));
            print(buffer.read(1000))
            # if cmd == 0x03:
            #     connection_id = struct.unpack("!I", buffer.read(4)); 
            #     server_link.new_connection(buffer_id)
            # elif cmd == 0x04:
            #     connection_id = struct.unpack("!I", buffer.read(4)); 
            #     server_link.end_connection(buffer_id)
            # else:
            #     RNS.log("invalid command on master " + str(cmd))
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

