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
# import asyncio_socks_server


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

def main():
    parser = argparse.ArgumentParser(description="A reticulum ip proxy")
    # parser.add_argument("command", choices=["client","server","discovery"])
    parser.add_argument("--configdir", default=None, help="Reticulum config directory (default ~/.reticulum)")
    parser.add_argument("--identity", default=None, help="reticulum identity")

    subparsers = parser.add_subparsers(dest='subcommand')

    parser_server = subparsers.add_parser("server")

    parser_client = subparsers.add_parser("client")
    parser_client.add_argument("destination");
    

    args = parser.parse_args()
    print(args)

    rns = RNS.Reticulum(configdir=args.configdir);

    if args.identity != None:
        print("given identity")
        if os.path.isfile(args.identity):
            identity = RNS.Identity.from_file(args.identity)
            if identity is None:
                raise SystemExit(f"could not read identity file {args.identity}")
    else:
        identity = RNS.Identity();

    if args.subcommand == "server":
        server.Server(identity);
    elif args.subcommand == "client":
        client_connection = client.Client(convert_str_to_destination(args.destination))
        socks.SocksProxyServer(client_connection)
    elif args.subcommand == "discovery":
        print("discovering i guess");



    print(f"identity hash: {identity.hash.hex()}")

    discovery.discover(rns)

    time.sleep(1);

        
    while True:
        time.sleep(1);
        
    

if __name__ == "__main__":
    main()

print("exit");
