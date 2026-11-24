import argparse
import time
from utility import *

class SocksOptionClient:
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
    def parse_args(cls, initial_args,  additional_args):
        self = cls()
        self.destination = initial_args.destination

        self.options = [];

        parser = argparse.ArgumentParser(prog='client')
        subparsers = parser.add_subparsers(help='idk what', dest='option')

        socks = subparsers.add_parser('socks')
        socks.add_argument("socks_host")

        forward = subparsers.add_parser('forward')
        forward.add_argument("remote_host")
        forward.add_argument('local_host', help='bar help')
        forward.add_argument('--udp', help='bar help') ## defaults to tcp if not specified

        filter_arg_list = []
        for arg in additional_args:
            if arg == "forward":
                filter_arg_list.append([])
            elif arg == "socks":
                filter_arg_list.append([])
            filter_arg_list[-1].append(arg) 

        for filter_arg in filter_arg_list:
            print(filter_arg)
            options, additional_args = parser.parse_known_args(filter_arg)
            if options.option == "socks":
                self.options.append(SocksOptionClient(options))
            elif options.option == "forward":
                self.options.append(ForwardOptionClient(options))
            else:
                print(f"invalid settings {additional_args} {options}")
                raise Exception


        return self

    def print(self):
        print(f"Client:")
        print(f"    Destination: {self.destination}")
        for option in self.options:
            option.print()
