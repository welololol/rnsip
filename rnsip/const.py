## SOCKS 

# We also use CMD_CONNECT and CMD_UDP_ASSOCIATE to denote if a connection is tcp or udp.
CMD_CONNECT = 0x01
CMD_BIND = 0x02
CMD_UDP_ASSOCIATE = 0x03

ATYP_EXIT = 0x00
ATYP_IPV4 = 0x01
ATYP_ALL = 0x02
ATYP_DOMAINNAME = 0x03
ATYP_IPV6 = 0x04

REP_SUCCEEDED = 0x00
REP_FAILURE = 0x02

SOCKS_VERSION = 0x05

## MASTER BUFFER

AUTH_PASS = 0x01
ACCEPT_AND_ANNC = 0x02
NEW_CONNECTION = 0x03
END_CONNECTION = 0x04



# ANNOUNCEMENT 

ANN_FORWARDED = 0x02

ANN_OTHER_DESTINATION = 0x10
ANN_LXMF = 0x11
ANN_NOMADNET = 0x12

# Announcement Flags global
# 
ANN_FLAG_REQUIRE_IDENTITY = 0b10000000

 
# Announcement filter Forward

# lower byte of the two bytes
FILTER_FLAG_INVERSE          = 0b1000000
FILTER_FLAG_CONNECT          = 0b0100000
FILTER_FLAG_BIND             = 0b0010000 # might go unused be instead be used for something else
FILTER_FLAG_UDP_ASSOCIATE    = 0b0001000

FILTER_FLAG_STATE_SPEEDS     = 0b0000100 # if to include both upspeed and downspeed

# these two bits are for all the port combinations
FILTER_PORT_BITS =             0b0000011

FILTER_FLAG_PORT_ALL         = 0b0000011 
FILTER_FLAG_PORT_SINGULAR    = 0b0000001
FILTER_FLAG_PORT_RANGE       = 0b0000010  # not sure about this one
FILTER_FLAG_PORT_CUSTOM      = 0b0000000  # we balling

# upper two bytes
FILTER_UPPER_BITS_FLAGS      = 0b1110000

# DEFAULTS

DEFAULT_UPSPEED_SOCKS = 100000
DEFAULT_DOWNSPEED_SOCKS = 100000

DEFAULT_UPSPEED_FORWARD = 100000
DEFAULT_DOWNSPEED_FORWARD = 100000

## OTHER


DEFAULT_PACKET_SIZE = 8096 # reasonable compormise between python overhead and not having an given tcp stream get starved

# in minutes
DEFAULT_ANNOUNCEMENT_RATE = 90 

DEFAULT_CONNECTION_BUFFER = 25 # the amoutn of connections we are listening to just in case
