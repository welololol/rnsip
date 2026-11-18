import threading
import RNS
class ReticulumBufferWrapper: # Utility class because the reticulum callback thing is kinda ass to use otherwise and likes to break
    def __init__(self, channel, id):
        self.held = 0
        self.event = threading.Event()
        self.buffer = RNS.Buffer.create_bidirectional_buffer(id, id, channel, self.data_in);

    def data_in(self, len):
        print("new data in")
        print(len)
        self.held += len
        self.event.set()

    def read_exact(self, len_data): # weird fix to do make callback work. Reads that specific amount of bytes and waits
        # if there isn't enough bytes then wait (not impl yet but it'll probably be fine)
         
        while self.held < len_data:
            self.event.wait()
            self.event.clear()
            # print("read_exact again", len_data, self.held)

        print("read_exact", len_data, self.held)

        self.held -= len_data
        data = self.buffer.read(len_data)
        return data

    def read(self, len_data): # same as read_exact but without that extra case.
        while self.held == 0:
            self.event.wait()
            self.event.clear()

        data = self.buffer.read(len_data)
        self.held -= len(data or [])

        return data

    def write(self, data):
        return self.buffer.write(data)
    def flush(self):
        self.buffer.flush()
