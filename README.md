2

A proxy layer between reticulum and ip traffic

reticulum-ip allows for proxying of ip traffic through the reticulum network. The wire format and repo intentionally is as minimial as possible to avoid reinventing the wheel.

# Yea but is this really necessary?

Two parts to this one:

1, No, you shouldn't proxy ip traffic through reticulum if you don't have to, don't use this program to forward an ssh port when rnsh exists, the overhead is unnecessary and characterists like latency and stability will always be worse. However if you have no choice and want to use/host a program that only supports tcp/udp or require proxying out of a censored regime to the wider internet through the reticulum network, this will do the trick.

2, Yes, plenty of existing programs do this exact same thing (including one I've made myself), but one, most of those are currently unmaintained or use vibe coded rust backends (which will probably become incompatiable with the python impl at some point) which don't exactly use the reticulum channel/buffer api so their tcp streams corrupt really often on any interface with packet loss.

# Usage

# Techincal Detail

For simplicity's sake, reticulum-ip attempts to use socksv5 as the backend as much as possible. The port forwarding system works similarly to socksv5

## Socskv5 Implementation (tcp)

Now this gets a bit confusing as there is actually three different channels going on, one tcp connection from an application to your local socksv5 server running on localhost, A link connection between this reticulum-ip instances and another remote instance, and finally a connection between the remote instance and whatever you are wanting to connect to ip side. We will refer to these as client side, reticulum side and server side to attempt to reduce confusion.

### Connection

When the client connects to the server through a link, it first identifies self on the link.

#### Meta Buffer

This denotes id 0 for the buffer that deals with authentication as well as pointing the server to new buffers that get created when the client wishes to create another tcp stream so we can muxplex all our data through one link, theortically you could make a new link for every tcp/udp channel but that would double the startup latency so we just avoid that.

Commands

Auth_Pass: 0x01 sent by client, password length in two bytes then itself. If there is no password then the client should send  Auth_pass with a length of zero. If the client sends an invalid password, the link should be torn down immediately.
Accept_and_Annc: 0x02, two bytes length, confirms that the client has been accepted, returns the server's announcement data as defined in ## Announcement format (or optionally return a length of zero).
New_Buffer: 0x03, 4 byte id,  sent by client to denote that it wishes to use a certain buffer as a new tcp connection telling the server it should create a bidrectional buffer with that id for the client to accept. The server does no reply on the master buffer, instead only doing so on the newly created buffered to allow multiple tcp streams to be created at the same time.
End_buffer: 0x04: 4 byte id, sent by both client and server to notify the other side that the connection has been canceled. When used on a buffer that was elvated to udp, this then ends the udp socket associated.


#### Generic Buffer

When the reticulum-ip client creates a generic buffer it will create a socksv5 request exactly the same as the associated spec, and the reticulum-ip server will then send a reply that looks the exact same as the spec as well for simplicity.

##### Connection

After the connection reply is sent, the buffer is then fully used for sending and receiving tcp data. Only being torn down when the END_BUFFER command is sent with the buffer's associated id..

##### Bind

Not currently implemented, but rarely used by socksv5 applications anyways. Will be at some point but frankly by default you wouldn't want this enabled even if you are operating a public use socksv5 reticulum-ip instance.

##### Udp Associate

On client side, the virtual sockv5 server returns back a udp socket on localhost, which is then forwarded raw through a link interface as denoted below. The udp socket is open till the client tears down this buffer, which then.

## Wire Format

All data for reticulum-ip goes through a channel (as defined in the reticulum api) after a connection intilation which we will then multiplex all the sockv5 data through, note this is slightly worse performance and latency that rolling our own reliable transport ontop of a link, but given the bandwidth and latency of the reticulum network this isn't a massive issue.


if you wish to know more, I recommend you read the socksv5 spec as it's not a long read https://datatracker.ietf.org/doc/html/rfc1928

## Announcement Format.

the app name used is *ip.socksv5*,

I using https://msgpack.org/ was considered (which is the standard for rnsd, nomadnet and mainline applications like partyline) however we already minpulate raw byte streams so it's easier to just work with that and python's built in struct.pack method, not to mention that for announcements we only have 465 bytes to work with and have to send everything about the server plus potential strings the user includes and we wanna be network efficient if we can help it.


appdata = Name:str Description:str, UpSpeed:int, DownSpeed:int, {Contact | Socksv5 | Forwarded}, 

lower 0x80 is used for actual configuration.

End: 0x00, denotes the end of the announcemet, note that in actual annoucement packets, we don't actually include this at the end as it is implied by size of the announcement anyways so internally we just add in a 0x00 byte at the end for convenience. We do however send the null byte on Accept_and_Annc
Socksv5: 0x01, {UpSpeed, DownSpeed, Flags (allow private, allow public, passworded, more undefined, allow udp, allow bind)}
Forwarded: 0x02, {Flags (udp, tcp, ipv4|ipv6|hostname|none), binary of ipv4,ipv6,hostname or none for local, port, description:str}(don't implement that the none functionality for now)

upper 0x80 is used for contact and additional data.

Lxmf 0x80: {LXMF Destination , string}
Nomadnet 0x81: {NOMADNET Destination , string}
Other Destination 0x82: {Reticulum Destination , string} 

All destinations are stored in 16 bytes.

note that every single in here is a pascal stirng meanign that they are limited to 256 bytes. 

In each "silo (or whatever I should call them)", there can be optional data

Note that reticulum's max announcement app_data size is 465 bytes or 465 characters minus overhead, so any description you put should be a few sentences at worst, you will be warned if app data does not fit however.

# Goals

- Stability
- Simplicity
- Minimialising network traffic/overhead
- Performance
- Extensibility.

In that order

Note that any message not in #Wire Format is intentionally undefined, futures implementations may add support for additional features if they wish, but they should support the main functionality in #Wire Format with the capabilities of the server/client being transmited on first handshake.

also note that while it's not one of the top goals, the overhead is pretty minimal with tcp (at least using the reticulum api), udp in the specific case of binding to one port and ip, as the destination ip and port is sent with every single packet which a decent amount of overhead to a packet with only a few bytes of data, this is just some weird consequence of the socksv5 spec and the python implementation I'm using. You could probably add some SINGLE_BIND_UDP buffer system that restructs the ip and port so that it's a little bit more efficient, this would probably most effect
