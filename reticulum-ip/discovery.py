import threading
import RNS
from RNS.vendor import umsgpack as msgpack

class discover:
    def __init__(self, rns):
        print("discovery enabled")
        threading.Thread(target=self.worker,args = (rns,), daemon=False).start()

    def worker(self, rns):
        a = AnnouncementHandler()
        RNS.Transport.register_announce_handler(a)

class AnnouncementHandler:
    def __init__(self):
        # self.aspect_filter = None;
        self.aspect_filter = "ip.server";

    def received_announce(self, destination_hash, announced_identity, app_data):
        # RNS.log(
            # "Received an announce from "+
            # RNS.prettyhexrep(destination_hash),
            # RNS.prettyhexrep(announced_identity)
        # )
        # unpacked = msgpack.unpackb(app_data)

        if app_data:
            print(str(msgpack.unpackb(app_data)) + " from " + RNS.prettyhexrep(destination_hash))


