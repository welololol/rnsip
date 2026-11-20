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
from settings import *
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

    subparsers = parser.add_subparsers(dest='subcommand')

    parser_server = subparsers.add_parser("server")
    parser_server.add_argument("--name");
    parser_server.add_argument("--lxmf");
    parser_server.add_argument("--nomadnet");
    parser_server.add_argument("--description");
    parser_server.add_argument("--password");

    parser_client = subparsers.add_parser("client")
    parser_client.add_argument("destination");

    parser_discovery = subparsers.add_parser("discovery")
    parser_discovery.add_argument("idk");

    namespace ,extra_args = parser.parse_known_args();
    subcommand = namespace.subcommand; 

    print(namespace, extra_args, subcommand)
    rns = RNS.Reticulum(configdir=namespace.configdir);



    if subcommand == "client":
        settings = ClientSettings.parse_args(namespace, extra_args)
        client_connection = client.Client(settings)
        print("connection")
        for option in settings.options:
            print("option", option)
            if isinstance(option, ForwardOptionClient):
                print("forward")
                forward_connection = forward.TCPPortForward(option, client_connection)
            elif isinstance(option, SocksOptionClient):
                print("socks")
                socks.SocksProxyLocal(option, client_connection)
            else:
                print("done?")
    elif subcommand == "server":
        settings = ServerSettings.parse_args(namespace,extra_args)
        server_runner = server.Server(settings)





    # if args.subcommand == "server":
    #     server.Server(identity);
    # elif args.subcommand == "client":
    #     client_connection = client.Client(convert_str_to_destination(args.destination))
    #     socks.SocksProxyServer(client_connection)
    #     forward.TCPPortForward(client_connection, "127.0.0.1", 25565, "127.0.0.1", 25565)
    # elif args.subcommand == "discovery":
    #     print("discovering i guess");



    # print(f"identity hash: {identity.hash.hex()}")

    # discovery.discover(rns)

    # time.sleep(1);

        
    while True:
        time.sleep(1);
        


if __name__ == "__main__":
    main()

print("exit");
