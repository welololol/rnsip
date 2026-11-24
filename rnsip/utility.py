import ipaddress
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
        l = len(data)
        a = self.buffer.write(data)
        if a != l:
            print(f"MISMATCH {l} {a}")
        self.buffer.flush()

    def flush(self):
        self.buffer.flush()


class ConnectionType:
    # host:port and then udp/tcp pair.
    # host can be anythign in the host type
    def __init__(self, type, host, port):
        self.type = type
        self.host = host
        self.port = port

    @classmethod
    def read_buf(cls, read_func, cannonise=False):
        b = read_func(3);
        connection_response = struct.unpack("!BBx",b);
        version = connection_response[0] ## we don't really bother too much checking this.
        type = connection_response[1]

        host = HostType.read_buf(read_func, cannonise=cannonise)        

        port = struct.unpack("!H", read_func(2))[0];
        # print(f"Connection info: {version},{type},{host.atyp},{host.hostname}:{port}")
        return cls(type,host,port)

    @classmethod
    def from_str_and_type(cls, string, type):
        tuple = string.split(":")
        if len(tuple) == 1: ## user just put in a port, so we assume they mean localhost
            port = tuple[0]
            host = "127.0.0.1"
        else:
            host = tuple[0]
            port = tuple[1]
            
        port = int(port)
        
        return cls(type, HostType.from_str(host), port)

    def write(self):
        b = bytearray([])
        
        b.extend(struct.pack("!BBx",SOCKS_VERSION, self.type))
        b.extend(self.host.write())

        b.extend(struct.pack("!H",self.port))
        print(b)
        return b

    def __str__(self):
        if self.type == CMD_CONNECT:
            return f"{self.host.hostname}:{self.port} TCP"
        else:
            return f"{self.host.hostname}:{self.port} UDP"

class HostType:
    def __init__(self, atyp, hostname):
        self.atyp = atyp
        self.hostname = hostname # a string btw

    @classmethod
    def read_buf(cls, read_func, cannonise=False):
        connection_response = struct.unpack("!B",read_func(1));
        atyp = connection_response[0]

        if atyp == ATYP_EXIT:
            return None
        elif atyp == ATYP_IPV4: ## ipv4 host
            hostname = socket.inet_ntoa(read_func(4))
        elif atyp == ATYP_ALL:
            hostname = ""
        elif atyp == ATYP_DOMAINNAME: ## hostname host
            host_size = struct.unpack("!B",read_func(1))[0];
            data = read_func(host_size)
            hostname = data.decode("utf-8");
        elif atyp == ATYP_IPV6: # ipv6 host
            hostname = socket.inet_ntop(socket.AF_INET6, read_func(16))
        else:
            print("invalid for some reason")
            while True:
                print(read_func(1))
        
        return cls(atyp,hostname)

    @classmethod
    def from_str(cls, host):
        if host == "all":
            return cls(ATYP_ALL, "")
        elif host == "localhost":
            return cls(ATYP_IPV4, "127.0.0.1")

        else:
            try:
                ip = ipaddress.ip_address(host)
                if ip.version == 4:
                    return cls(ATYP_IPV4, ip.compressed)
                else:
                    return cls(ATYP_IPV6, ip.compressed)
                    
            except:
                return cls(ATYP_DOMAINNAME, host)


    def __str__(self):
        if self.atyp == ATYP_ALL:
            return "all"
        return self.hostname

    def write(self):
        b = bytearray([self.atyp])
        if self.atyp == ATYP_EXIT:
            return b
        elif self.atyp == ATYP_IPV4: ## ipv4 host
            b.extend(ipaddress.IPv4Address(self.hostname).packed)
        elif self.atyp == ATYP_ALL:
            return b
        elif self.atyp == ATYP_DOMAINNAME:
            b.extend(struct.pack("!B",len(self.hostname)))
            b.extend(self.hostname.encode("utf-8"))
        elif self.atyp == ATYP_IPV6:
            b.extend(ipaddress.IPv6Address(self.hostname).packed)
        else:
           print("write function not working")
        return b

    def filter(self, ip_addr , domain):
        print(self.atyp, self.hostname,  ip_addr, domain)
        print(ip_addr == self.hostname)
        print(type(ip_addr), type(self.hostname))
        if self.atyp == ATYP_DOMAINNAME:
            return domain == self.hostname
        elif self.atyp == ATYP_ALL:
            return True
        elif self.atyp == ATYP_IPV4:
            return ip_addr == self.hostname
        elif self.atyp == ATYP_IPV6:
            return ip_addr == self.hostname
        else:
            print("nothign to filter")
            return False




class PortFilter:
    # possible types. All, Singular (includes port number), Range (two port numbers), Other (other stuff which is reserved for now)
    # type is stored as the binary for convenience

    def __str__(self):
        if self.type == FILTER_FLAG_PORT_ALL:
            return ""
        elif self.type == FILTER_FLAG_PORT_SINGULAR:
            return f":{self.ports}" 

    def __init__(self, type, ports):
        # ports can be a single int, a list, range or other depending on the specifics
        self.type = type
        self.ports = ports

    @classmethod
    def from_str(cls, str):
        self = cls(FILTER_FLAG_PORT_SINGULAR, int(str))
        return self

    @classmethod
    def read_buf(cls, read_func, stated_type):
        if stated_type == FILTER_FLAG_PORT_ALL:
            return cls(stated_type, None)
        elif stated_type == FILTER_FLAG_PORT_SINGULAR:
            return cls(stated_type, struct.unpack("!H", read_func(2))[0])
        else:
            print("uh oh")

    def write(self):
        if self.type == FILTER_FLAG_PORT_ALL:
            return bytearray([]) #
        else:
            return struct.pack("!H", self.ports)

    def filter(self, port):
        if self.type == FILTER_FLAG_PORT_ALL:
            return True
        elif self.type == FILTER_FLAG_PORT_SINGULAR:
            return self.ports == port
        else:
            return False



class BufferTcpExchange():
    def read_from_reticulum_side(self):
        while True:
            data = self.wrapped_buffer.read(DEFAULT_PACKET_SIZE);
            print(f"read {len(data)}")
            if len(data) == 0:
                print("shit is hitting the fan a little")
                break
            try:
                self.socket.sendall(data)
            except OSError: #if we can't send to socket, it's cooked then return.
                self.teardown_otherside()
                break
        self.teardown_socket()

    def write_to_reticulum_side(self):
        while True:
            try:
                data = self.socket.recv(DEFAULT_PACKET_SIZE);
                print(f"write {len(data)}")
                if len(data) == 0: # if no more data socket is probably cooked so cancel
                    self.teardown_otherside()
                    break
                else:
                    self.wrapped_buffer.write(data);
            except Exception as exception:
                break

        self.teardown_socket()

    # if the other side told us to close or something happened locally
    def teardown_socket(self):
        print(f" end socket {self.wrapped_buffer.id}")
        try:
            self.socket.shutdown(socket.SHUT_RDWR)
        except OSError: # shutting down a socket that is closed gives us this so.
            pass
        finally:
            self.socket.close()
        ## generally the threads will teardown themselves at this piont.

    # if our local side's socket disconnects we should notify the other side
    def teardown_otherside(self):
        if not self.already_deleted:
            self.destroy_buffer_func();
            self.already_deleted = True;

    def __init__(self, wrapped_buffer, socket, destroy_buffer_func):
        self.socket = socket
        self.wrapped_buffer = wrapped_buffer;
        self.already_deleted = False;
        self.destroy_buffer_func = destroy_buffer_func

        self.read_thread = threading.Thread(target=self.read_from_reticulum_side,args = (), daemon=True);
        self.write_thread = threading.Thread(target=self.write_to_reticulum_side,args = (), daemon=True);

        self.read_thread.start();
        self.write_thread.start();

class ConnectionSpeeds(): # downspeed followed by upspeed always
    def __init__(self, upspeed, downspeed):
        self.upspeed = upspeed
        self.downspeed = downspeed

    def write(self):
        b = bytearray([])
        b.extend(struct.pack("!LL", self.downspeed,self.upspeed))
        return b

    def __str__(self):
        return f"{self.downspeed}B/s down, {self.upspeed}B/s up"

    @classmethod
    def read_buf(cls, read_func):
        downspeed, upspeed = struct.unpack("!LL", read_func(8))
        return cls(upspeed, downspeed)


def convert_str_to_destination(destination_hexhash):
    try:
        dest_len = (RNS.Reticulum.TRUNCATED_HASHLENGTH//8)*2
        if len(destination_hexhash) != dest_len:
            raise ValueError(
                "Destination length is invalid, must be {hex} hexadecimal characters ({byte} bytes).".format(hex=dest_len, byte=dest_len//2)
            )
        des_bytes = bytes.fromhex(destination_hexhash)

        if not RNS.Transport.has_path(des_bytes):
            print("requesting path")
            RNS.Transport.request_path(des_bytes)
            RNS.Transport.await_path(des_bytes)
            

        
        server_identity = RNS.Identity.recall(des_bytes)
        print(f"server identity {server_identity}")
        return RNS.Destination(server_identity, RNS.Destination.OUT, RNS.Destination.SINGLE, "ip", "socksv5");

    except Exception as e:
        RNS.log("Invalid destination entered. Check your input!")
        RNS.log(str(e)+"\n")



def read_exact_from_socket(socket, n):
    buff = bytearray(n)
    pos = 0
    while pos < n:
        cr = socket.recv_into(memoryview(buff)[pos:])
        if cr == 0:
            raise EOFError
        pos += cr
    return buff

# don't wanna require python 3.15 yet so we just manually make the function which might be slow i guess but it's fine.
def take_bytes(buffer, n):
    data = bytes(buffer[:n + 1])
    del buffer[:n + 1]
    return data
