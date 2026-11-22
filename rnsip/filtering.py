import socket
import ipaddress

def filter_ip_based_on_settings(connection_type, settings):
    host = connection_type 
    socket.getaddrinfo(
    connection.get
    socket.get2
    pass

def convert_to_ip(host, port):
    info = socket.getaddrinfo(host, port)[0] # we could loop through these, but nah, just pick the first ip and go with it for now
    ## usually favours ipv6 over ipv4 anyways which is probably better?
    ip_string = info[4][0]
    return ipaddress.ip_address(ip_string)
    
