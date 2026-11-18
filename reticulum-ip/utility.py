import threading
import struct
import socket
import RNS
from const import *

class ReticulumBufferWrapper: # Utility class because the reticulum callback thing is kinda ass to use otherwise and likes to break
    def __init__(self, channel, id):
        self.buffer = RNS.Buffer.create_bidirectional_buffer(id, id, channel, self.data_in);
        self.event = threading.Event()
        self.id = id
        self.held = 0

    def data_in(self, len):
        self.held = len
        self.event.set()

    def read_exact(self, len_data): # weird fix to do make callback work. Reads that specific amount of bytes and waits
        # if there isn't enough bytes then wait (not impl yet but it'll probably be fine)

        while self.held < len_data:
            self.event.wait()
            self.event.clear()


        data = self.buffer.read(len_data)
        if data == None:
            return bytes([])

        self.held -= len(data)
        return data
        # return self.buffer.read(len_data)

    def read(self, len_data): # same as read_exact but without that extra case.
        while self.held == 0:
            self.event.wait()
            self.event.clear()

        data = self.buffer.read(len_data)
        if data == None:
            return bytes([])

        self.held -= len(data)
        return data

        # return self.buffer.read1(len_data)

    def write(self, data):
        a = self.buffer.write(data)
        self.buffer.flush()

    def flush(self):
        self.buffer.flush()


class ConnectionType:
    # Takes buffer stream, and gives connection
    #
    # allows passing a read and write function so we can pass this to a buffer or a socket transparently
    # 
    def __init__(self, cmd, atyp, host, port):
        self.cmd = cmd
        self.atyp = atyp
        self.host = host
        self.port = port

    @classmethod
    def read_buf(cls, read_func):
        connection_response = struct.unpack("!BBxB",read_func(4));
        version = connection_response[0] ## we don't really bother too much checking this.
        cmd = connection_response[1]
        atyp = connection_response[2]

        if atyp == ATYP_IPV4: ## ipv4 host
            host = socket.inet_ntoa(read_func(4))
        elif atyp == ATYP_DOMAINNAME: ## hostname host
            host_size = struct.unpack("!B",read_func(1))[0];
            data = read_func(host_size)
            host = data.decode("utf-8");
        elif atyp == ATYP_IPV6: # ipv6 host
            host = socket.inet_ntop(socket.AF_INET6, read_func(16))
        else:
            print("ERROR")
        
        port = struct.unpack("!H", read_func(2))[0];
        print(f"Connection info: {version},{cmd},{atyp},{host}:{port}")
        return cls(cmd,atyp,host,port)


    def write(self, write_func):
        write_func(struct.pack("!BBxB",SOCKS_VERSION, self.cmd,self.atyp))
        print("write")
        if self.atyp == ATYP_DOMAINNAME:
            write_func(struct.pack("!B",len(self.host)))
            write_func(self.host.encode("utf-8"))
        else:
            pass

        write_func(struct.pack("!H",self.port))


