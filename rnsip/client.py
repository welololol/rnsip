import RNS
import time
import threading
import struct
import socket
from utility import *
from const import *

class Client:
    def __init__(self, settings):
        destination_bytes = convert_str_to_destination(settings.destination)
        RNS.Link(destination_bytes, established_callback=self.new_link)

    def new_link(self, link):
        self.client_link = ClientLink(link)


class ClientLink:
    def __init__(self, link):
        self.id_rolling = 1;
        self.link = link
        self.buffers = {}
        self.channel = link.get_channel();
        self.master_buffer = MasterBufferClient(self, self.channel)

    def new_connection(self, tcp_socket_connection, connection_type=None):
        # techincally two connections could happen at once and overwrite the id but I'm not worried bout that rn
        id = self.id_rolling + 1
        self.id_rolling = id;

        buffer = ReticulumBufferWrapper(self.channel, id)
        # time.sleep(0.01)
        self.master_buffer.new_connection(id);

        print(f"making buffer {id} (remove delay at some point)")
        time.sleep(0.01)
        self.buffers[id] = SocksClientConnection(tcp_socket_connection, buffer, connection_type=connection_type)
        
    def close(self, id):
        self.master_buffer.new_connection(id);


class MasterBufferClient:

    def master_interaction_thread(self):

        self.buffer.write(bytes([AUTH_PASS,0x00,0x00])); ## should be a password thing here later. But this is basically saying no pass

        a = self.buffer.read_exact(3)
        announce_cmd_return = struct.unpack("!BH",a);
        cmd = announce_cmd_return[0]
        if cmd != ACCEPT_AND_ANNC:
            print("shit has hit the fan")
            pass

        announce_len  = announce_cmd_return[1]
        announce_data = self.buffer.read_exact(announce_len)

        # by this point, the connection has be initialised.
        # the only thing the client needs to listen for is the server tearing down a connection
        # the only thing the server is listening for, is the client creating connections and also tearing them down
        # these are independant in the sense that we aren't looking for a reply, because the reply is sent in a different
        # buffer than the master one. So while possibly confusing, we don't have any syncing queue here, we just send
        # requests directly and assume that it'll be fine.
        
        # BUT, we need a loop to receive server data (for the tearing down of connections if the server does that)

        while True:
            cmd_return = struct.unpack("!B",self.buffer.read_exact(1));
            cmd = announce_cmd_return[0]


    def __init__(self, client_link , channel):
        self.buffer = ReticulumBufferWrapper(channel, 1)

        threading.Thread(target=self.master_interaction_thread,args = (), daemon=True).start();

    def new_connection(self, id):
        new_connection = struct.pack("!BI", NEW_BUFFER, id); 
        self.buffer.write(new_connection)
        self.buffer.flush()

    def close_connection(self, id):
        new_connection = struct.pack("!BI", END_BUFFER, id); 
        self.buffer.write(new_connection)
        self.buffer.flush()

class SocksClientConnection:
    def handshake(self, connection_type=None):
        print("new")
        if connection_type == None:
            def recv_wrapped(len_data):
                return read_exact_from_socket(self.tcp_socket,len_data)

            connection_type = ConnectionType.read_buf(recv_wrapped)
            generated_connection = None;
        else:
            generated_connection = True;
            print("no connection type by default")

        print(f"Connection {str(connection_type)}")

        self.buffer.write(connection_type.write())
        
        # the server then only replies with if the command is succesful given by the standard
        # however it doesn't reply with the destination port or whatever cause it's irrevalant for the most part
        # so we instead just fake it back to the client

        server_response = struct.unpack("!B", self.buffer.read_exact(1))[0]
        if server_response != REP_SUCCEEDED:
            print(f"not actually succeed hold up {server_response}")

        if generated_connection == None:
            self.tcp_socket.sendall(bytes([SOCKS_VERSION, REP_SUCCEEDED, 0x00, ATYP_IPV4, 0,0,0,0, 0,0]))
        # gives some bogus response equivalent to "yea we gonna sent all your traffic to 0.0.0.0:0,
        # don't worry about it the operation was successful. trust me bro.

        BufferTcpExchange(self.buffer, self.tcp_socket)

    def flush_initial(self):
        # occasionally we will send data to the remote buffer
        # before it has actually initialised, which causes problems
        # so we just keep flushing the bytes till it works out
        for i in range(1,25):
            self.buffer.flush();
            time.sleep(0.01)
            self.buffer.flush();


    
    def __init__(self,tcp_socket, buffer, connection_type=None):
        self.buffer = buffer;
        self.tcp_socket = tcp_socket

        threading.Thread(target=self.flush_initial,args = (), daemon=True).start();
        threading.Thread(target=self.handshake,args = (), kwargs={"connection_type":connection_type}, daemon=True).start();

