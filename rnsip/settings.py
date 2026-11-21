from socketserver import TCPServer
import argparse
import os
import time
from utility import *
from const import *


class SocksOptionServer:
    type = ANN_SOCKSV5 
    def __init__(self, args):
        print(args)
        self.upspeed = int(args.upspeed or DEFAULT_UPSPEED_SOCKS)
        self.downspeed = int(args.downspeed or DEFAULT_DOWNSPEED_SOCKS)
    def print(self):
        print(f"    Socks:");
        print(f"        Upspeed: {self.upspeed}B/s");
        print(f"        Downspeed: {self.downspeed}B/s");

    # we don't include the type in the encoding.
    def to_bytes(self):
        return struct.pack("!ll", self.upspeed, self.downspeed)
        
    @classmethod
    def from_bytes(cls, read_func):
        args = argparse.Namespace(); # just for consistency
        args.upspeed,args.downspeed = struct.unpack("!ll", read_func(8))
        return cls(args)


class ForwardOptionServer:
    type = ANN_FORWARDED
    def __init__(self, args):
        self.upspeed = int(args.upspeed or DEFAULT_UPSPEED_FORWARD)
        self.downspeed = int(args.downspeed or DEFAULT_DOWNSPEED_FORWARD)
        self.connection = ConnectionType.from_str_and_type(args.hostname, CMD_CONNECT)

    def print(self):
        print(f"    Forward:");
        print(f"        Upspeed: {self.upspeed}B/s");
        print(f"        Downspeed: {self.downspeed}B/s");
        print(f"        Connection: {str(self.connection)}");

    def to_bytes(self):
        temp  = bytearray(struct.pack("!ll", self.upspeed, self.downspeed))
        temp.extend(self.connection.write());
        return temp
        
    @classmethod
    def from_bytes(cls, read_func):
        args = {}
        args["upspeed"],args["downspeed"] = struct.unpack("!ll", read_func(8))
        args["connection"] = ConnectionType.read_buf(read_func)
        return cls(args)

LIST_OF_OPTIONS_SERVER = [SocksOptionServer,ForwardOptionServer]

class ServerSettings:
    # any arguements we don't transmit through announcements have an underscore. such as the password itself.
    # 
    @classmethod
    def parse_args(self, initial_args,  additional_args):
        self.name = initial_args.name or ""
        self.description = initial_args.description or ""
        self._password = initial_args.password or ""
        self._announcement_rate = int(initial_args.announcement_rate or DEFAULT_ANNOUNCEMENT_RATE)
        if initial_args.identity != None:
            print("given identity")
            if os.path.isfile(initial_args.identity):
                identity = RNS.Identity.from_file(initial_args.identity)
                if identity is None:
                    raise SystemExit(f"could not read identity file {initial_args.identity}")
                self._identity_bytes = identity
        else:
            self._identity_bytes = RNS.Identity();

        self.options = [];

        parser = argparse.ArgumentParser(prog='client')
        subparsers = parser.add_subparsers(help='idk what', dest='option')

        socks = subparsers.add_parser('socks')
        socks.add_argument('--allow-private', help='bar help')
        socks.add_argument('--allow-localhost', help='bar help')
        socks.add_argument('--allow-udp', help='bar help')
        socks.add_argument('--allow-tcp', help='bar help')
        socks.add_argument('--allow-bind', help='bar help')
        socks.add_argument('--upspeed', help='bar help')
        socks.add_argument('--downspeed', help='bar help')

        # socks: (--allow-private, --allow-localhost, --allow-udp, --allow-tcp, --allow-bind --upspeed, --downspeed --description),
        # forward ([hostname:]port --upspeed --downspeed --description)
        forward = subparsers.add_parser('forward')
        forward.add_argument("hostname")
        forward.add_argument('--upspeed', help='bar help')
        forward.add_argument('--downspeed', help='bar help')
        forward.add_argument('--tcp', help='default')
        forward.add_argument('--udp', help='default')

        while additional_args:
            options, additional_args = parser.parse_known_args(additional_args)
            if options.option == "socks":
                self.options.append(SocksOptionServer(options)) 
            elif options.option == "forward":
                self.options.append(ForwardOptionServer(options))

        return self()

    def to_bytes(self):

        b = bytearray()
        # will silently trim the strings if they are above 256 characters but who cares really
        b.extend(struct.pack("B", min(len(self.name),255)))
        b.extend(self.name.encode("utf-8")[:256])
        b.extend(struct.pack("B", min(len(self.description),255)))
        b.extend(self.description.encode("utf-8")[:256])

        for option in self.options:
            b.extend(bytes([option.type]))
            b.extend(option.to_bytes())
        return b

    @classmethod
    def from_bytes(cls, read_func):
        # strings are dynamic so we have to do some funky stuff here
        name_size = struct.unpack("B", read_func(1))[0]
        cls.name = read_func(name_size).decode("utf-8")

        desc_size = struct.unpack("B", read_func(1))[0]
        cls.description = read_func(desc_size).decode("utf-8")

        # I seriously need better variable names look at this
        cls.options = []
        while True:
            option_type = struct.unpack("B", read_func(1))[0]
            print(option_type)
            if option_type == 0x00:
                print("break")
                break
            else:
                for option_class in LIST_OF_OPTIONS_SERVER:
                    print(option_type, option_class.type)
                    if option_type == option_class.type:
                        cls.options.append(option_class.from_bytes(read_func))

        return cls()


                    # b.extend(option.to_bytes())
        
    def print(self, owner):
        print(f"{owner}:")
        print(f"    Name: {self.name}")
        print(f"    Description: {self.description}")
        for option in self.options:
            option.print()


class SocksOptionClient:
    type = ANN_SOCKSV5 
    def __init__(self, args):
        # self.downspeed = args.downspeed
        # self.allow-private = private
        # self.allow-localhost = localhost
        # self.allow-udp = udp
        # self.allow-tcp = tcp
        # self.allow-bind = bind
        self.socks_host = ConnectionType.from_str_and_type(args.socks_host, CMD_CONNECT)
    def print(self):
        print(f"    Socks:");
        print(f"        Socks Host: {str(self.socks_host)}");


class ForwardOptionClient:
    type = ANN_FORWARDED
    def __init__(self, args):
        self.local_connection = ConnectionType.from_str_and_type(args.local_host, CMD_CONNECT)
        self.remote_connection = ConnectionType.from_str_and_type(args.remote_host, CMD_CONNECT)

    def print(self):
        print(f"    Forward:");
        print(f"        Local Connection: {str(self.local_connection)}");
        print(f"        Remote Connection: {str(self.local_connection)}");

    
class ClientSettings:
    @classmethod
    def parse_args(self, initial_args,  additional_args):
        self.destination = initial_args.destination

        self.options = [];

        parser = argparse.ArgumentParser(prog='client')
        subparsers = parser.add_subparsers(help='idk what', dest='option')

        socks = subparsers.add_parser('socks')
        socks.add_argument('socks_host', help='bar help')

        forward = subparsers.add_parser('forward')
        forward.add_argument("remote_host")
        forward.add_argument('local_host', help='bar help')
        forward.add_argument('--udp', help='bar help') ## defaults to tcp if not specified

        while additional_args:
            options, additional_args = parser.parse_known_args(additional_args)
            if options.option == "socks":
                print("option socks")
                self.options.append(SocksOptionClient(options))
            elif options.option == "forward":
                print("forward")
                self.options.append(ForwardOptionClient(options))


        return self()

    def print(self):
        print(f"Client:")
        print(f"    Destination: {self.destination}")
        for option in self.options:

            option.print()
