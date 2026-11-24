from socketserver import TCPServer
import argparse
import os
import sys
import time
from utility import *
from const import *
from argparse import Namespace

class Filter:
    def __init__(self, host_filter, connection_speed, inverse, connect, udp_associate, bind, port_filter):
        self.host_filter = host_filter
        self.connection_speed = connection_speed
        self.inverse = inverse
        self.connect = connect
        self.udp_associate = udp_associate
        self.bind = bind
        self.port_filter = port_filter

    @classmethod
    def from_args(cls, args):
        connection_speed =  ConnectionSpeeds(args.upspeed, args.downspeed)
        split = args.hostname.rsplit(":",1)
        if len(split) == 2:
            host_filter = HostType.from_str(split[0])
            port_filter = PortFilter.from_str(split[1])
        else:
            if split[0].isdigit():
                host_filter = HostType(ATYP_IPV4,"127.0.0.1")
                port_filter = PortFilter.from_str(split[0])
            else:
                host_filter = HostType.from_str(split[0])
                port_filter = PortFilter(FILTER_FLAG_PORT_ALL, None)

        inverse = False;
        connect = True;
        bind = False;
        udp_associate = False;
        return cls(host_filter, connection_speed, inverse, connect, bind, udp_associate, port_filter)

    def print(self ,number = "?"):
        flags = []
        if self.connect:
            flags.append("TCP Connect")
        if self.udp_associate:
            flags.append("UDP Associate")
        print(f"    Filter [{number}]:");
        print(f"        Host: {str(self.host_filter)}{str(self.port_filter)}");
        print(f"        Speeds: {str(self.connection_speed)}");
        print(f"        Flags: [{','.join(flags)}]");
        # print(f"        Host: {str(self.connection)}");

    def to_bytes(self):
        flag_byte = 0b0000000;
        if self.inverse:
            flag_byte |= FILTER_FLAG_INVERSE
        if self.connect:
            flag_byte |= FILTER_FLAG_CONNECT
        if self.connection_speed != None :
            flag_byte |= FILTER_FLAG_STATE_SPEEDS

        flag_byte |= self.port_filter.type

        temp = bytearray([])
        temp.extend(self.host_filter.write())
        temp.extend(bytes([flag_byte]))
        temp.extend(self.port_filter.write())

        if self.connection_speed != None:
            temp.extend(self.connection_speed.write())

        # temp  = bytearray(struct.pack("!ll", self.upspeed, self.downspeed))
        # temp.extend(self.connection.write());
        return temp
        
    @classmethod
    def from_bytes(cls, read_func):
        host_filter = HostType.read_buf(read_func)
        if host_filter == None:
            return None
        flag_byte = read_func(1)[0]
        port_filter = PortFilter.read_buf(read_func, FILTER_PORT_BITS & flag_byte)
        inverse = FILTER_FLAG_INVERSE & flag_byte > 0
        connect = FILTER_FLAG_CONNECT & flag_byte > 0
        bind = FILTER_FLAG_BIND & flag_byte > 0
        udp_associate = FILTER_FLAG_UDP_ASSOCIATE & flag_byte > 0

        if FILTER_FLAG_STATE_SPEEDS & flag_byte > 0:
            connection_speed = ConnectionSpeeds.read_buf(read_func)

        return cls(host_filter ,connection_speed, inverse, connect, bind, udp_associate, port_filter)

    def is_hit(self, ip_addr, hostname, port, method):
        print("in1")
        if (method == CMD_CONNECT) & self.connect | (method == CMD_BIND) & self.bind | (method == CMD_UDP_ASSOCIATE) | self.udp_associate :
            print("in2")
            port_accepted = self.port_filter.filter(port)
            host_accepted = self.host_filter.filter(ip_addr,hostname)
            print(port_accepted, host_accepted)
            return port_accepted and host_accepted
        
        return False
        

class ServerSettings:
    # any arguements we don't transmit through announcements have an underscore. such as the password itself.
    # 
    @classmethod
    def parse_args(self, initial_args,  additional_args):
        self._announcement_rate = initial_args.announcement_rate 
        self.name = initial_args.name
        self.description = initial_args.description 
        self.requires_identity  = initial_args.requires_identity 
        self._password = initial_args.password

        if initial_args.identity != None:
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

        allow = subparsers.add_parser('allow')
        allow.add_argument("hostname")
        allow.add_argument('--upspeed', help='bar help', type=int)
        allow.add_argument('--downspeed', help='bar help', type=int)
        allow.add_argument('--tcp', help='default')
        allow.add_argument('--udp', help='default')

        rolling_upspeed   = 100000
        rolling_downspeed = 100000

        filter_arg_list = []
        for arg in additional_args:
            if arg == "allow":
                filter_arg_list.append([])
            filter_arg_list[-1].append(arg)

        for filter_args in filter_arg_list:
            options, additional_args = parser.parse_known_args(filter_args)
            if options.option == "allow":
                rolling_upspeed = options.upspeed or rolling_upspeed
                rolling_downspeed = options.downspeed or rolling_downspeed
                options.upspeed = rolling_upspeed
                options.downspeed = rolling_downspeed
                self.options.append(Filter.from_args(options)) 
            else:
                print(f"invalid settings {additional_args} {options}")
                raise Exception

        return self()

    def to_bytes(self):
        b = bytearray()

        # services like rmap.world check for pascal strings as the first thing, so we do this so they can get the name properly. even if the rest of the thing is in binary
        # will silently trim the strings if they are above 256 characters but who cares really
        b.extend(struct.pack("!B", min(len(self.name),255)))
        b.extend(self.name.encode("utf-8")[:256])

        ## least significant 3 bits are for version, which is 0 for now
        # Most siginificant is for if you need to identify yourself
        flag_byte = 0x00
        if self.requires_identity:
            flag_byte |= ANN_FLAG_REQUIRE_IDENTITY

        b.extend(bytes([flag_byte]))

        b.extend(struct.pack("!B", min(len(self.description),255)))
        b.extend(self.description.encode("utf-8")[:256])

        for option in self.options:
            b.extend(option.to_bytes())
        return b

    @classmethod
    def from_bytes(cls, read_func):
        self = cls()
        # strings are dynamic so we have to do some funky stuff here
        name_size = struct.unpack("!B", read_func(1))[0]
        self.name = read_func(name_size).decode("utf-8")

        flag_byte = struct.unpack("!B", read_func(1))[0]
        self.requires_identity = flag_byte & ANN_FLAG_REQUIRE_IDENTITY > 0

        desc_size = struct.unpack("!B", read_func(1))[0]
        self.description = read_func(desc_size).decode("utf-8")

        # I seriously need better variable names look at this
        self.options = []
        while True:
            filter = Filter.from_bytes(read_func)
            if filter == None:
                break
            else:
                self.options.append(filter)

        return self

    def print(self, owner):
        print(f"{owner}:")
        print(f"    Name: {self.name}")
        print(f"    Description: {self.description}")
        flags = []
        if self.requires_identity:
            flags.append("Requires Identity")
        print(f"    Flags: [{','.join(flags)}]")
        for (i, option) in enumerate(self.options):
            option.print(number = (i + 1))
