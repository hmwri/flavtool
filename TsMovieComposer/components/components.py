from TsMovieComposer.boxs.container import ContainerBox
from TsMovieComposer.boxs.leaf import *
import io
class EvalComponent:
    def __init__(self, parsed: Box):
        self.parsed = parsed


class TrackComponent(EvalComponent):
    def __init__(self, parsed: ContainerBox):
        super().__init__(parsed)
        self.header: TkhdBox = parsed["tkhd"]
        self.media: MediaComponent = MediaComponent(parsed["mdia"])




class MediaComponent(EvalComponent):
    def __init__(self, parsed: ContainerBox):
        super().__init__(parsed)
        self.header: MdhdBox = parsed["mdhd"]
        self.handler: HdlrBox = parsed["hdlr"]
        self.media_info: MediaInfoComponent = MediaInfoComponent(parsed["minf"])




class MediaInfoComponent(EvalComponent):
    def __init__(self, parsed: ContainerBox):
        super().__init__(parsed)
        if parsed["smhd"] is not None:
            self.header: SmhdBox = parsed["smhd"]
        elif parsed["vmhd"] is not None:
            self.header: VmhdBox = parsed["vmhd"]
        else:
            self.header = None
        self.data_information: ContainerBox = parsed["dinf"]

        self.sample_table = SampleTableComponent(parsed["stbl"])


class SampleTableComponent(EvalComponent):
    def __init__(self, parsed: ContainerBox):
        super().__init__(parsed)

        self.chunk_offset: StcoBox = parsed["stco"]
        self.sample_size: StszBox = parsed["stsz"]
        self.sample_description: StsdBox = parsed["stsd"]
        self.time_to_sample: SttsBox = parsed["stts"]
        self.sample_to_chunk: StscBox = parsed["stsc"]


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

class MediaData():
    def __init__(self, media_type:str,
                 data:list[ChunkData]):
        self.media_type = media_type
        self.data: list[ChunkData] = data


    @classmethod
    def from_mdat_box(cls, mdat_box: MdatBox, sample_table: SampleTableComponent, media_type:str,
                  streaming=False) -> 'MediaData':
        offset = mdat_box.begin_point

        sample_table = sample_table
        byte_data = mdat_box.body
        sample_i = 0
        next_sample_to_chunk_i = 0
        samples_per_chunk = 0
        data: list[ChunkData] = []
        for chunk_i, chunk_offset in enumerate(sample_table.chunk_offset.chunk_to_offset_table, start=1):

            sample_to_chunk_table = sample_table.sample_to_chunk.sample_to_chunk_table
            if next_sample_to_chunk_i < len(sample_to_chunk_table) \
                    and sample_to_chunk_table[next_sample_to_chunk_i].first_chunk == chunk_i:
                samples_per_chunk = sample_to_chunk_table[next_sample_to_chunk_i].samples_per_chunk
                next_sample_to_chunk_i += 1
            samples: list[SampleData] = []
            chunk_inside_offset = 0

            begin_time = cls.__get_time_of_sample(sample_i, sample_table)
            for j in range(samples_per_chunk):
                sample_size = sample_table.sample_size.sample_size if sample_table.sample_size.sample_size != 0 else \
                    sample_table.sample_size.sample_size_table[sample_i]
                sample_start = (chunk_offset - offset) + chunk_inside_offset
                if streaming:
                    sample = StreamingSampleData(chunk_offset + chunk_inside_offset, sample_size)
                else:
                    sample = SampleData(byte_data[sample_start: sample_start + sample_size])
                samples.append(sample)
                chunk_inside_offset += sample_size
                sample_i += 1

            end_time = cls.__get_time_of_sample(sample_i - 1,sample_table,criteria="end")
            data.append(ChunkData(samples,media_type, begin_time=begin_time, end_time=end_time))
        return cls(media_type, data)

    @classmethod
    def __get_time_of_sample(cls, sample_i, sample_table: SampleTableComponent, criteria="start"):
        table = sample_table.time_to_sample.time_to_sample_table
        t = 0
        sample_n = 0
        for td in table:
            for i in range(td.sample_count):
                if sample_n == sample_i:
                    if criteria == "start":
                        return t
                    else:
                        return t + td.sample_delta
                t += td.sample_delta
                sample_n += 1



