import io

from .sample import SampleData


class ChunkData:
    def __init__(self, samples: list[SampleData], media_type: str,sample_description=1, begin_time=0, end_time=0):
        self.samples = samples
        self.media_type = media_type
        self.begin_time = begin_time
        self.end_time = end_time
        self.sample_description = sample_description

    def get_size(self):
        size = 0
        for sample in self.samples:
            size += len(sample)
        return size

    def print(self):
        print()
        print(f"Chunk - {self.media_type} begin time{self.begin_time}, end_time{self.end_time}, description{self.sample_description}")

        for sample in self.samples:
            sample.print()

    def write(self, buffer: io.BytesIO):
        for sample in self.samples:
            buffer.write(sample.data)
