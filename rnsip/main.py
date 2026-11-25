import RNS
from RNS.vendor import umsgpack
import os
import time
import socket
import argparse
import discovery
import socks
import client
import server
import forward
from server_settings import *
from client_settings import *
# import asyncio_socks_server



def main():
    # commmands: (in all these caess, hostname can be an ipv4 or ipv6 address as well and defaults to localhost when not included)
    # 
    # --configdir --identity --background_discovery
    # 
    # server
    #
    # --name --description --nomadnet --lxmf  --password
    # 
    # socks: (--allow-private, --allow-localhost, --allow-udp, --allow-tcp, --allow-bind --upspeed, --downspeed --description),
    # forward ([hostname:]port --upspeed --downspeed --description)
    # 
    # client 1:destination: --password
    # socks (--destination [hostname:]port))
    # connect (--local [hostname:]port --remote [hostname:]port)
    # 
    # discovery:
    # continous (--silent)
    # display (--json)
    # 
    parser = argparse.ArgumentParser(description="A reticulum ip proxy")
    parser.add_argument("--configdir", default=None, help="Reticulum config directory (default ~/.reticulum)")
    parser.add_argument("--identity", default=None, help="reticulum identity")
    parser.add_argument("--debug-level", default=3, help="reticulum identity")

    subparsers = parser.add_subparsers(dest='subcommand')

    parser_server = subparsers.add_parser("server")
    parser_server.add_argument("--requires-identity", action="store_true");
    parser_server.add_argument("--name", default="");
    parser_server.add_argument("--description", default="");
    parser_server.add_argument("--password", default="");
    parser_server.add_argument("--announcement-rate", type=int, default=DEFAULT_ANNOUNCEMENT_RATE);

    parser_client = subparsers.add_parser("client")
    parser_client.add_argument("destination");
    parser_client.add_argument("--password", default="");
    parser_client.add_argument("--transmit-identity");

    parser_discovery = subparsers.add_parser("discovery")
    parser_discovery.add_argument("idk");

    namespace ,extra_args = parser.parse_known_args();
    subcommand = namespace.subcommand; 
    print(namespace, extra_args)

    rns = RNS.Reticulum(configdir=namespace.configdir, loglevel=int(namespace.debug_level));

    if subcommand == "client":
        settings = ClientSettings.parse_args(namespace, extra_args)
        client_connection = client.Client(settings)
        for option in settings.options:
            if isinstance(option, ForwardOptionClient):
                forward_connection = forward.TCPPortForward(option, client_connection)
            elif isinstance(option, SocksOptionClient):
                socks.SocksProxyLocal(option, client_connection)
            else:
                print("properly implement errors later")
                raise Exception
    elif subcommand == "server":
        settings = ServerSettings.parse_args(namespace,extra_args)
        settings.print("me")
        set = settings.to_bytes()
        set.extend(bytearray([0x00]))

        print("hm")
        print(set)
        def read_buffer(n):
            if n > len(set):
                raise Exception
            data = bytes(set[:n])
            del set[:n]        
            return data

        new_settings = settings.from_bytes(read_buffer)
        new_settings.print("other me")
        server_runner = server.Server(settings)
    else:
        print("INVALID COMMAND")

    # print(f"identity hash: {identity.hash.hex()}")
       
    while True:
        time.sleep(1);
        print(list(threading.enumerate())) # for debugging
        
if __name__ == "__main__":
    main()

print("exit");
