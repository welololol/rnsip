import RNS
import time
import threading
import struct
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
        self.channel = link.get_channel();
        print("buffer")
        self.master_buffer = MasterBufferClient(self, self.channel)

    def new_connection(self, tcp_socket_connection, id):
        self.id_rolling += 1
        self.buffer = RNS.Buffer.create_bidirectional_buffer(self.id_rolling,self.id_rolling, self.channel);
        self.master_buffer.new_connection(id);
        connection = SocksClientConnection(tcp_socket_connection,self.buffer)
        

    def data_in(self, len):
        print("new data in")
        print(len)
        print(self.buffer.read(len))


class MasterBufferClient:

    def master_interaction_thread(self):
        while True:
            # self.buffer.write(bytes([0x01,0x00,0x00])); ## shoudl be a password thing here later
            print("write more")
            self.buffer.write(b" leople weroiwerweirwe jklwerjwerklj" * 10) ; ## shoudl be a password thing here later
            self.buffer.flush()
            # print(self.buffer.read(1000))
            time.sleep(0.1)
            # print("huh")

        return 

        a = buffer.read1(3)
        print(a)
        announce_cmd_return = struct.unpack("!BH",a);
        cmd = announce_cmd_return[0]
        if cmd != 0x02:
            print("ERROR")

        announce_len  = announce_cmd_return[1]
        announce_data = buffer.read(announce_len)
        # by this point, the connection has be initialised.
    def __init__(self, client_link , channel):
        self.buffer = ReticulumBufferWrapper(channel, 1)

        threading.Thread(target=self.master_interaction_thread,args = (), daemon=True).start();

    def new_connection(self, id):
        new_connection = struct.pack("!BI", 0x03, id) 
        self.buffer.write(new_connection)


class SocksClientConnection:
    def __init__(self,tcp_socket_connection, buffer):
        self.buffer = buffer;

        while True:
            new_data = tcp_socket_connection.recv(456);
            print("new data")
            print(new_data)
            buffer.write(new_data);

            sending_data = buffer.read(1200);
            print("new data 2")
            print(sending_data)
            tcp_socket_connection.sendall(sending_data)

