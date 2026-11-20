from socketserver import TCPServer
import argparse
import os
from utility import *
from const import *

class SocksOptionServer:
    type = ANN_SOCKSV5 
    def __init__(self, args):
        self.description = args.description
        self.upspeed = args.upspeed
        self.downspeed = args.downspeed
        # self.allow-private = private
        # self.allow-localhost = localhost
        # self.allow-udp = udp
        # self.allow-tcp = tcp
        # self.allow-bind = bind
        # self.allow_localhost = 
    def print(self):
        print(f"    Socks:");
        print(f"        Description: {self.description}b/s");
        print(f"        Upspeed: {self.upspeed}b/s");
        print(f"        Downspeed: {self.downspeed}b/s");


class ForwardOptionServer:
    type = ANN_FORWARDED
    def __init__(self, args):
        self.upspeed = args.upspeed
        self.downspeed = args.downspeed
        self.connection = ConnectionType.from_str_and_type(args.hostname, CMD_CONNECT)
        self.description = args.description

    def print(self):
        print(f"    Forward:");
        print(f"        Description: {self.description}b/s");
        print(f"        Upspeed: {self.upspeed}b/s");
        print(f"        Downspeed: {self.downspeed}b/s");
        print(f"        Connection: {str(self.connection)}");

class ServerSettings:
    # any arguements we don't transmit through announcements have an underscore. such as the password itself.

    @classmethod
    def parse_args(self, initial_args,  additional_args):
        self.name = initial_args.name
        self.description = initial_args.description
        self.lxmf = initial_args.lxmf
        self.nomadnet = initial_args.nomadnet
        self._password = initial_args.password
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
        socks.add_argument('--description', help='bar help')

        # socks: (--allow-private, --allow-localhost, --allow-udp, --allow-tcp, --allow-bind --upspeed, --downspeed --description),
        # forward ([hostname:]port --upspeed --downspeed --description)
        forward = subparsers.add_parser('forward')
        forward.add_argument("hostname")
        forward.add_argument('--upspeed', help='bar help')
        forward.add_argument('--downspeed', help='bar help')
        forward.add_argument('--tcp', help='default')
        forward.add_argument('--udp', help='default')
        forward.add_argument('--description', help='bar help')

        while additional_args:
            options, additional_args = parser.parse_known_args(additional_args)
            if options.option == "socks":
                self.options.append(SocksOptionServer(options))
            elif options.option == "forward":
                self.options.append(ForwardOptionServer(options))

        return self()
        
    def print(self, owner):
        print(f"{owner}:")
        print(f"    Name: {self.name}")
        print(f"    Description: {self.description}")
        print(f"    LXMF: {self.lxmf}")
        print(f"    Nomadnet: {self.nomadnet}")
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
