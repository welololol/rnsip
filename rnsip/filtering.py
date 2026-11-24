from const import *
import socket
import ipaddress

def filter_ip_based_on_settings(connection_type, settings):
    host_string = connection_type.host.hostname;
    host_type = connection_type.host.atyp;
    print(host_string,host_type)

    ip_addr = None # could be ipv4 or ipv6, we don't really translate tbh
    hostname = None 
    if host_type == ATYP_IPV4 or host_type == ATYP_IPV6:
        # no hostname in this case
        ip_addr = ipaddress.ip_address(host_string).compressed
    elif host_type == ATYP_DOMAINNAME:
        hostname = host_string
        if True: ## this would be if you want DNS
            ip_addr = convert_to_ip_string(hostname, connection_type.port) 
    else:
        # we don't accept ranges or anything
        return None, None

    last_hit_filter = None
    filters = settings.options 
    print("in filtering")

    for (i, filter) in enumerate(filters):
        print(f"not HIT {i}:{filter}") 
        if filter.is_hit(ip_addr, hostname, connection_type.port, connection_type.type):
            print(f"HIT {i}:{filter}") 
            last_hit_filter = filter
    
    print(f"filter {last_hit_filter}")
    if last_hit_filter == None:
        return None, None

    if last_hit_filter.inverse == True:
        return None, None

    return ip_addr or hostname, last_hit_filter.connection_speed; # nothing is acceptable, return nil.

def convert_to_ip_string(host, port):
    print(host,port)
    info = socket.getaddrinfo(host, port)[0] # we could loop through these, but nah, just pick the first ip and go with it for now
    ## usually favours ipv6 over ipv4 anyways which is probably better?
    ip_string = info[4][0]
    return ip_string
    
