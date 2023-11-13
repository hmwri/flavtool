from TsMovieComposer.analyzer.components import SampleTableComponent
from .sample import SampleData, StreamingSampleData
from .chunk import ChunkData
from TsMovieComposer.parser.boxs.leaf import MdatBox


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