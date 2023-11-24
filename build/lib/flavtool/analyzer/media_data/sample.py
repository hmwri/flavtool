class SampleData:
    def __init__(self, data: bytes, delta:int):
        self.data = data
        self.delta = delta

    def print(self):
        print("-", len(self.data), end=",")

    def __len__(self):
        return len(self.data)


class StreamingSampleData(SampleData):
    def __init__(self, start:int, length:int, delta:int):
        super().__init__(b'', delta)
        self.start = start
        self.length = length



    def print(self):
        print(f"- {self.start} ~ {self.length}", end=",")

    def __len__(self):
        return self.length







