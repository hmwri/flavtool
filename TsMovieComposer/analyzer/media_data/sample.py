class SampleData:
    def __init__(self, data: bytes):
        self.data = data

    def print(self):
        print("-", len(self.data), end=",")

    def __len__(self):
        return len(self.data)


class StreamingSampleData(SampleData):
    def __init__(self, start, length):
        super().__init__(b'')
        self.start = start
        self.length = length
        self.delta = None
        self.start_time = None
        self.data = None
        self.i = 0
        self.sample_i=0


    def set_info(self, sample_i, start_time, delta):
        self.sample_i = sample_i
        self.start_time = start_time
        self.delta = delta

    def set_data(self, data):
        self.data = data

    def get_frame_data(self, i):
        self.i = 0
        return self.data[i]

    def get_next_frame_data(self):
        self.i += 1
        if self.i == self.data.shape[0]:
            return None
        result = self.data[self.i]
        return result

    def print(self):
        print(f"- {self.start} ~ {self.length}", end=",")

    def __len__(self):
        return len(self.data)







