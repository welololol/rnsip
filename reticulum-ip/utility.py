import threading
import RNS
class ReticulumBufferWrapper: # Utility class because the reticulum callback thing is kinda ass to use otherwise and likes to break
    def __init__(self, channel, id):
        self.buffer = RNS.Buffer.create_bidirectional_buffer(id, id, channel, self.data_in);
        self.event = threading.Event()
        self.id = id
        # data = self.buffer.peek(12312312323)
        self.held = 0 # we just assume a high number at first cause we don't know if there is a backlog
        


    def data_in(self, len):
        print(f"new data in {len} {self.id}")
        self.held = len
        self.event.set()

    def read_exact(self, len_data): # weird fix to do make callback work. Reads that specific amount of bytes and waits
        # if there isn't enough bytes then wait (not impl yet but it'll probably be fine)

         
        while self.held < len_data:
            self.event.wait()
            self.event.clear()
            print("read_exact again", len_data, self.held)

        print("read_exact", len_data, self.held, self.id)

        data = self.buffer.read(len_data)
        if data == None:
            return bytes([])

        self.held -= len(data)
        return data
        # return self.buffer.read(len_data)

    def read(self, len_data): # same as read_exact but without that extra case.
        print(f"held: {self.held}")
        while self.held == 0:
            self.event.wait()
            self.event.clear()

        print("data incoming i guess")
        data = self.buffer.read(len_data)
        if data == None:
            return bytes([])

        self.held -= len(data)
        return data

        # return self.buffer.read1(len_data)

    def write(self, data):
        a = self.buffer.write(data)
        print(f"wrote {a}")
        self.buffer.flush()

    def write1(self, data):
        a = self.buffer.write(data)
        print(f"wrote no flush {a}")

    def flush(self):
        self.buffer.flush()
