> [!CAUTION]
> This is still being actively developed and may be insecure. Client side it should be safe to use however be wary of using this server side cause you may allow random reticulum arbitary ability to access any ports in your private/local network.

> [!NOTE]
> While I want to make a stable protocol at some point, this will be unstable for the time being as I make a usable program

> [!NOTE]
> This readme is sorta a mess for now of my own thought process, don't trust anything you read here

reticulum-ip allows for proxying of ip traffic through the reticulum network. The wire format and repo intentionally is as minimial as possible to avoid reinventing the wheel.

## Yea but is this really necessary?

Two parts to this one:

1, No, you shouldn't proxy ip traffic through reticulum if you don't have to, don't use this program to forward an ssh port when rnsh exists, the overhead is unnecessary and characterists like latency and stability will always be worse. However if you have no choice and want to use/host a program that only supports tcp/udp or require proxying out of a censored regime to the wider internet through the reticulum network, this will do the trick.

2, Yes, plenty of existing programs do this exact same thing (including one I've made myself), but one, most of those are currently unmaintained or use vibe coded rust backends (which will probably become incompatiable with the python impl at some point) which don't exactly use the reticulum channel/buffer api so their tcp streams corrupt really often on any interface with packet loss.

## Usage

The lowest I've been able to load websites is about 10kb/s (and that's after waiting a while), with lowest being about 2kb/s before most services disconnect before more than a few packets go through

## Techincal Detail

For simplicity's sake, reticulum-ip attempts to use socksv5 as the backend as much as possible. The port forwarding system works similarly to socksv5

### Socskv5 Implementation (tcp)

Now this gets a bit confusing as there is actually three different channels going on, one tcp connection from an application to your local socksv5 server running on localhost, A link connection between this reticulum-ip instances and another remote instance, and finally a connection between the remote instance and whatever you are wanting to connect to ip side. We will refer to these as client side, reticulum side and server side to attempt to reduce confusion.

#### Connection

When the client connects to the server through a link, it first identifies self on the link.

##### Meta Buffer

This denotes id 0 for the buffer that deals with authentication as well as pointing the server to new buffers that get created when the client wishes to create another tcp stream so we can muxplex all our data through one link, theortically you could make a new link for every tcp/udp channel but that would double the startup latency so we just avoid that.

Commands

Auth_Pass: 0x01 sent by client, password length in two bytes then itself. If there is no password then the client should send  Auth_pass with a length of zero. If the client sends an invalid password, the link should be torn down immediately.
Accept_and_Annc: 0x02, two bytes length, confirms that the client has been accepted, returns the server's announcement data as defined in ## Announcement format (or optionally return a length of zero).
New_Buffer: 0x03, 4 byte id,  sent by client to denote that it wishes to use a certain buffer as a new tcp connection telling the server it should create a bidrectional buffer with that id for the client to accept. The server does no reply on the master buffer, instead only doing so on the newly created buffered to allow multiple tcp streams to be created at the same time.
End_buffer: 0x04: 4 byte id, sent by both client and server to notify the other side that the connection has been canceled. When used on a buffer that was elvated to udp, this then ends the udp socket associated.


##### Generic Buffer

When the reticulum-ip client creates a generic buffer it will create a socksv5 request exactly the same as the associated spec, and the reticulum-ip server will then send a reply that looks the exact same as the spec as well for simplicity.

###### Connection

After the connection reply is sent, the buffer is then fully used for sending and receiving tcp data. Only being torn down when the END_BUFFER command is sent with the buffer's associated id..

###### Bind

Not currently implemented, but rarely used by socksv5 applications anyways. Will be at some point but frankly by default you wouldn't want this enabled even if you are operating a public use socksv5 reticulum-ip instance.

###### Udp Associate

On client side, the virtual sockv5 server returns back a udp socket on localhost, which is then forwarded raw through a link interface as denoted below. The udp socket is open till the client tears down this buffer, which then.

### Wire Format

All data for reticulum-ip goes through a channel (as defined in the reticulum api) after a connection intilation which we will then multiplex all the sockv5 data through, note this is slightly worse performance and latency that rolling our own reliable transport ontop of a link, but given the bandwidth and latency of the reticulum network this isn't a massive issue.


if you wish to know more, I recommend you read the socksv5 spec as it's not a long read https://datatracker.ietf.org/doc/html/rfc1928

### Announcement Format.

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

## Goals

- Stability
- Simplicity
- Minimialising network traffic/overhead
- Performance
- Extensibility.

In that order

Note that any message not in #Wire Format is intentionally undefined, futures implementations may add support for additional features if they wish, but they should support the main functionality in #Wire Format with the capabilities of the server/client being transmited on first handshake.

also note that while it's not one of the top goals, the overhead is pretty minimal with tcp (at least using the reticulum api), udp in the specific case of binding to one port and ip, as the destination ip and port is sent with every single packet which a decent amount of overhead to a packet with only a few bytes of data, this is just some weird consequence of the socksv5 spec and the python implementation I'm using. You could probably add some SINGLE_BIND_UDP buffer system that restructs the ip and port so that it's a little bit more efficient, this would probably most effect

# working notes

''
Announcements/Forwarding stuff

instead of having a forward and socks "option", actually we'll now call it, nah option is fine actually for a name.

We have just a general "forward" thing, which denotes a set of addresses, and some flags. 

For instance, we could have a forward option that denotes all public addresses. or one that denotes private ip addresses.
Or another that denotes all addresses, or addresses of a certain regex or a certain ipv4/6 range or localhost or whatever.
 
followed by one flag byte. And that byte would include if an upspeed or downspeed value is gonna be in the following bytes.
one bit if there is a string attached (allow for description if the address range is strange, or you need to say that all
ip addresses in this range are getting proxied by tor or something)
one bit if the address is actually blocked. (ie, inverse, filters out instead of allows)
3 bits for connect, udp and bind. if those are avaliable (note that for each of these, if a certain filter)
one bit for something to do with ports. (you can either allow them all, specific one, other.)
maybe if we need more options, we could use some of the bits in atyp, if we don't plan on using more than 32 different options. 

for upspeed and downspeed value, the noted value applies to all ips mentioned, for instance, if we have a proxy that had a slow 10kb/s up
and downspeed connection. and then a local monero node with 1mb/s on port , any data send outbound would go towards the 10kb/s
limit, and so if you were downloading many thing from public ip addresses, they all share that 10kb/s limit, where as you coudl do
1mb/s on the monero node and do 10kb/s on some random background thing. if a filter allowed 127.0.0.1:80

To save on a byte, we could denote all lower 128 values to be addresses or ranges, and the upper be things like nomadnet or string.
the lower 128 would share with the atyp ones.

## all possible atyp options

0x00: END OF OPTIONS
0x01: ipv4 address
0x02: localhost (only included to save 4 bytes for common addresses, should also be understood by the reticulum bridge and transmited back on the other side so that instead transmitting 5 bytes to connect to a local address, we just use 1 byte because I reckon using localhost addresses will be common enough that this will help save a little bandwidth)
0x03: domain name (socks spec)
0x04: ipv6 address
0x05: ipv4 block
0x06: ipv6 block
0x07: regex (applying to the string form of whatever input you give it including domain names and ips)
0x08: public ip addresses (based on python definition)
0x09: private ip addresses (just make the user state which ones? inverse of public anywyas so we could remove)
0x0A: loopback addresses (different than localhost, shorthand for the 127.0.0.1/8 block, not sure if this is actually useful)
0x0B: Everything/All.
0x0C: reserved
0x0D: Unknown?
0x0E: Custom but without the string? So, like, unknown basically, could do anything
0x0F: Custom (maybe have like a string so the operator can explain the filtering type)

hell sounds like we could fit everything in 4 bits, giving us 11 bits of flag given we want to squeeze in stuff like nomadnet destination

0x10: LXMF Destination: 16 destination bytes
0x11: Nomadnet destination: 16 destination bytes
0x12: Other destionation: 16 destination bytes + str that explains what they are for.
0x13: idk.

we could fit all these into the 16 values above which I'll think about but for now it's not necessary.

so, each option looks like this 0bFFFFFFF,FFFDAAAA
with F being a flag
D chocing if we are making a filter (we should call it filters)
AAAA being option type of filter or whatever.

so in the command it'd look like this
rnsip server --requires-identity allow public-addresses:{0-1024} --upspeed 10kb/s --downspeed 10kb/s  filter youtube.com:443, allow localhost:25565

--upspeed 0b/s --downspeed 0b/s is the same as filtering kinda, but then that rqeuires 8 bytes for just filtering one address so that isn't worth it.
still not worth it.

so all the flags are.
0x01: Inverse, if the filter should do the inverse of the range described. ie, only allow to not localhost


On second thought, the inverse flag isn't actually that useful.
also we should go from most specified to least specific order, both because it makes it easier to iterate through
but also if upspeed and downspeed are specified, they should just be infinite, so if you are port forwarding a service, but
also allow connecting to the wider web, in the case that you allow infinite traffic to your service and then limited to the web
you only have to include --upspeed --downspeed a single time. instead of twice, saving on bytes.
, also the str flag doesn't really make sense, it's free to just include text in the description andor instead as 0x10 destination additional data thing

we could also limit the range of --upspeed and downspeed and make it 3 or even 2 bytes. because we don't have to represent it super accurately. this is for later to think about.

internally we should just call this all filters, but filter command means we don't allow it,
and pass/whatever-word-i-find-that-accurately-describes means that we allow the block of addresses.

Only additional thing is that for each filter, have an optional socksv5 proxy, so for instance when sending traffic to the public internet, we just send it to the tor network
Don't bother telling the client that we have a proxy in the settings (except for description where the operator can do that)

## upspeed and downspeed

for max downspeed or upspeed, we denote a blocked_time. which denotes how long we should pause before allowing another packet.

every time we send/receive a packet, we do blocked_time += bits / bitrate, so we if we send 1kB of data throgh with a limit
of 10/kBs, we pause sending/receiving for 0.1 seconds (using time.sleep)

There would also be a average-time or buffer or whatever value, because the above only implies that the average speed since the connection has started has to be 10/kBs but allows for higher bursts, so instead blocked_time = max(blocked_time + bits/ bitrate, time.current_time() - buffer_time), if buffer time is 1 second, that means that there is no filtering as long as the connection on average in the last 1 second is nto mroe than 10kb/s, meaning that the user could send 10kb in a single instant and be fine if had not being using traffic previously.

Maybe some considering for reducing the amount of data we trying to send if the max bitrate is low, like if it's 1mb/s then
send 10KB of data at a time, but if it's like 10kb/s per second, maybe just send 455 bytes at once. Thing is that the reticulum
link itself could have a max of a certain amount of bytes.


based on the filters, you could have a filter_id, ie, so if the is for all public web traffic is 10kb/s the server will limit it, but also
have the client limit it as well because it'll know which filter it is under and thus what datarates to stick to
so that the client only tries to send data as quickly as the server will send it out. This isn't necessary persay but it stops an
application from being confused because it send out all it's tcp data in like 0.1 seconds but it hasn't heard a reply yet in 10 seconds
because the reticulum link is only 500b/s, and the initial send is still going through the wire even though the application thinks
that all the data has been accepted already. should also smooth out reticululm traffic a little, as if the upspeed limit is
1024B/s, there's no reason to send a 100mb file through a poor i2p/backbone link at full speed if the end point is limited.

Same thing could maybe apply reticulum side, I'm not quite sure what happens if reticulum cannot send out packets fast enough


the atyp byte should be before the flag byte. because only some atyp options have flags after them, and the 0x00 byte shouldn't carry with it an entire new byte for no reason.


## TUN interface

For later but, this would be basically jsut be a server, client thing similar to the socks thing.
every link gets it's own ip address, controlled by the server (server sends back it's ip, and the client just has to deal with it)

 If a packet came in, if it's to another interface then
it'll be sent back into the program, else it'll just be sent to the device's local gateway, aka, being pretty similar to a vpn.

Only protection this grants is that we'll only send ip packets to the corresponding identity and only allow ip backs if the receipt is the one who sent it.
However, that's more of a bandwidth thing than a security thing, and everything else you just use a commerical firewall.

The only thing that is that you should allow hooking in to an existing tun interface to make firewalling on the server easier.

Also adding some adhoc command in addition to server and client, where you just give a list of identities and ip addresses, and a tun interface is created for every one of them (or it's a single tun interface that you map everything to, either or), and each client creates a link to every other client that is online.

Also tell the user that they have to setup their own firewall,nat, or whatever to actually get this properly working and that's more effort.

see https://pypi.org/project/python-pytun/ https://www.gabriel.urdhr.fr/2021/05/08/tuntap/ for I get around to this.

## Tap

Tun would be the exact same, and would not be difficult at all to implement, but also would be very little reason to actually use one besides testing and coolness factor. Also kinda goes against the name rnsip cause that implies layer 3 and this is layer 2, but meh.

## preventing dns leaks

we don't want to resolve domain names if we don't have to. if the user sends google.com that's fine but if they send veryspecificwebsite.net they could find the server's
ip address.

Probably just a --do-not-resolve setting would be fine.

note that a hostname's ip address and the hostname itself could produce different results.

The filtering function should be this

def filter(domain, ipaddr)

if domain is present, ip addr will be unless --do-not-resolve-dns is on
if ip addr is present, that does not necessary mean domain is.


## other weird filtering issue

if you specify that all addresses are udp/tcp accessible with a low speed
but then also that localhost is accessible with tcp at a high speed, localhost
should then just not be accessible with udp at all. same with ports, if port 22 is
avaliable on 127.0.0.5 but not the loopback generallyvb
