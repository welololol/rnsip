import RNS
import time
import threading
import struct
import socket
from utility import *
from const import *

class Client:
    def __init__(self, settings):
        self.settings = settings
        self.client_link = None;
        self.destination_bytes = convert_str_to_destination(settings.destination)
        self.attempt_connection()

    def attempt_connection(self):
        RNS.Link(self.destination_bytes, established_callback=self.new_link, closed_callback=self.closed_link)

    def new_link(self, link):
        print(f"sucessfully connected to <{self.settings.destination}>")
        self.client_link = ClientLink(link)

    def closed_link(self, link):
        current_link = self.client_link # 90% sure it'll be the same ones as we close unless the code has really fucked up
        print(f"link has been broken {link} {current_link}")
        current_link.teardown()

        print("attempting reconnect")
        self.attempt_connection()

class ClientLink:
    def __init__(self, link):
        self.id_rolling = 1;
        self.connection_lock = threading.Lock()
        self.link = link
        self.connections = {}
        self.channel = link.get_channel();
        self.master_buffer = MasterBufferClient(self, self.channel)

    def new_connection(self, tcp_socket_connection, connection_type=None):
        # techincally two connections could happen at once and overwrite the id but I'm not worried bout that rn
        self.connection_lock.acquire()
        id = self.id_rolling + 1
        self.id_rolling = id;
        self.connection_lock.release()

        self.connections[id] = SocksClientConnection(tcp_socket_connection, self, id,  connection_type=connection_type)
        print(self.connections)
        
    def close_connection(self, id):
        self.master_buffer.close_connection(id);
        self.connections[id].teardown(internal=False)
        del self.connections[id];

    def teardown(self):
        RNS.log("TEARING DOWN LINK (kill all connections?)")
        for connection in self.connections.values():
            connection.teardown(internal=False) # we don't have to send stuff to the server to kill the connections
            # because we are breaking the link anyways

        self.link.teardown();

class MasterBufferClient:
    def master_interaction_thread(self):

        self.wrapper_buffer.write(bytes([AUTH_PASS,0x00,0x00])); ## should be a password thing here later. But this is basically saying no pass

        a = self.wrapper_buffer.read_exact(3)
        announce_cmd_return = struct.unpack("!BH",a);
        cmd = announce_cmd_return[0]
        if cmd != ACCEPT_AND_ANNC:
            print("shit has hit the fan")
            pass

        announce_len  = announce_cmd_return[1]
        announce_data = self.wrapper_buffer.read_exact(announce_len)

        # by this point, the connection has be initialised.
        # the only thing the client needs to listen for is the server tearing down a connection
        # the only thing the server is listening for, is the client creating connections and also tearing them down
        # these are independant in the sense that we aren't looking for a reply, because the reply is sent in a different
        # buffer than the master one. So while possibly confusing, we don't have any syncing queue here, we just send
        # requests directly and assume that it'll be fine.
        
        # BUT, we need a loop to receive server data (for the tearing down of connections if the server does that)

        while True:
            cmd_return = struct.unpack("!B",self.wrapper_buffer.read_exact(1));
            cmd = announce_cmd_return[0]


    def __init__(self, client_link , channel):
        self.wrapper_buffer = ReticulumBufferWrapper(channel, 1)

        threading.Thread(target=self.master_interaction_thread,args = (), daemon=True).start();

    def close_connection(self, id):
        new_connection = struct.pack("!BI", END_CONNECTION, id); 
        self.wrapper_buffer.write(new_connection)
        self.wrapper_buffer.flush()

class SocksClientConnection:
    def handshake(self, connection_type=None):
        if connection_type == None:
            def recv_wrapped(len_data):
                return read_exact_from_socket(self.tcp_socket,len_data)

            connection_type = ConnectionType.read_buf(recv_wrapped)
            generated_connection = None;
        else:
            generated_connection = True;


        self.buffer_wrapper.write(connection_type.write())
        
        # the server then only replies with if the command is succesful given by the standard
        # however it doesn't reply with the destination port or whatever cause it's irrevalant for the most part
        # so we instead just fake it back to the client

        server_response = struct.unpack("!B", self.buffer_wrapper.read_exact(1))[0]
        if server_response != REP_SUCCEEDED:
            print(f"not actually succeed hold up {server_response}")

        if generated_connection == None:
            self.tcp_socket.sendall(bytes([SOCKS_VERSION, REP_SUCCEEDED, 0x00, ATYP_IPV4, 0,0,0,0, 0,0]))
        # gives some bogus response equivalent to "yea we gonna sent all your traffic to 0.0.0.0:0,
        # don't worry about it the operation was successful. trust me bro.

        self.finished_handshake = True

        def destroy_buffer():
            self.client_link.close_connection(self.buffer_wrapper.id)

        self.exchange_buffer = BufferTcpExchange(self.buffer_wrapper, self.tcp_socket, destroy_buffer)

    def teardown(self, internal=True):
        # if internal then propagate upwards to clientlink so that the other side knows, if not just delete
        print(f"[{self.buffer_wrapper.id}] is being torn-down")
        if self.finished_handshake:
            self.exchange_buffer.teardown_socket()
        else:
            ## must be paused on handshake
            self.tcp_socket.close()
        if internal == True:
            self.client_link.close_connection_remote(self.buffer_wrapper.id)

    def flush_initial(self):
        # occasionally we will send data to the remote.exchange_buffer
        # before it has actually initialised, which causes problems
        # so we just keep flushing the bytes till it works out
        self.buffer_wrapper.flush();
        for i in range(1,25):
            time.sleep(0.01)
            self.buffer_wrapper.flush();

    
    def __init__(self,tcp_socket, client_link, buffer_id, connection_type=None):
        self.buffer_wrapper = ReticulumBufferWrapper(client_link.channel, buffer_id)
        self.tcp_socket = tcp_socket
        self.client_link = client_link
        self.finished_handshake = False

        threading.Thread(target=self.flush_initial,args = (), daemon=True).start();
        threading.Thread(target=self.handshake,args = (), kwargs={"connection_type":connection_type}, daemon=True).start();

