import io

from boxs.container import ContainerBox
from boxs.leaf import *
import numpy as np


class Composer:
    def __init__(self, parsed_box: ContainerBox):
        self.parsed = parsed_box
        box: ContainerBox
        for box in self.parsed["moov"].children:
            if box.box_type == "trak":
                subtype: str = box["mdia"]["hdlr"].component_subtype
                if subtype == "soun":
                    self.sound_track = TrackComponent(box)
                elif subtype == "vide":
                    self.video_track = TrackComponent(box)
        self.video_sample_table = self.video_track.media.media_info.sample_table
        self.video_media_data = MediaDataComponent(
            self.parsed["mdat"],
            self.video_sample_table,
            "video"
        )
        self.movie_header: MvhdBox = self.parsed["moov"]["mvhd"]
        self.sound_sample_table = self.sound_track.media.media_info.sample_table
        self.sound_media_data = MediaDataComponent(
            self.parsed["mdat"],
            self.sound_sample_table,
            "sound"
        )
        self.taste_track = None
        self.scent_track = None
        self.mdat: MdatBox = self.parsed["mdat"]

    def compose(self):
        # time_scale
        video_sps = self.video_track.media.header.time_scale
        sound_sps = self.sound_track.media.header.time_scale
        chunks: list[ChunkData] = []
        video_chunks = self.video_media_data.data
        sound_chunks = self.sound_media_data.data
        video_chunk_offsets = []
        sound_chunk_offsets = []
        sound_i = 0
        offset = 0
        for video_chunk in video_chunks:
            print(offset)
            video_chunk_offsets.append(offset)
            chunks.append(video_chunk)
            offset += video_chunk.get_size()
            while sound_i < len(sound_chunks) and sound_chunks[
                sound_i].begin_time / sound_sps <= video_chunk.end_time / video_sps:
                sound_chunk_offsets.append(offset)
                sound_chunk = sound_chunks[sound_i]
                chunks.append(sound_chunk)
                offset += sound_chunk.get_size()
                sound_i += 1
        while sound_i < len(sound_chunks):
            sound_chunk_offsets.append(offset)
            chunks.append(sound_chunks[sound_i])
            offset += sound_chunks[sound_i].get_size()
            sound_i += 1

        buffer = io.BytesIO()
        for chunk in chunks:
            chunk.write(buffer)
        buffer.seek(0)
        self.mdat.body = buffer.read()

        self.create_dummy_stco(len(video_chunks), stco=self.video_sample_table.chunk_offset)
        self.create_dummy_stco(len(sound_chunks), stco=self.sound_sample_table.chunk_offset)
        mdat, mdat_offset = self.parsed.get_mdat_offset()
        self.mdat.begin_point = mdat_offset
        self.video_sample_table.chunk_offset.chunk_to_offset_table = [vco + mdat_offset for vco in video_chunk_offsets]
        self.sound_sample_table.chunk_offset.chunk_to_offset_table = [sco + mdat_offset for sco in sound_chunk_offsets]
        print(self.sound_sample_table.chunk_offset)

    def create_dummy_stco(self, chunks_len: int, stco: StcoBox = None):
        if stco is None:
            return
        stco.number_of_entries = chunks_len
        stco.chunk_to_offset_table = []

    def add_taste_track(self, data: np.ndarray, fps: float, codec: str):
        now = (datetime.now() - datetime(1904, 1, 1)).total_seconds()

        sample_table = ContainerBox(
            box_type="stbl",
            children=[
                StsdBox(
                    number_of_entries=1,
                    sample_description_table=[
                        SampleDescription(

                        )
                    ]
                )
            ]
        )

        track_box = ContainerBox(
            box_type="trak",
            children=[
                TkhdBox(
                    box_type="tkhd",
                    creation_time=int(now),
                    modification_time=int(now),
                    duration=0,
                    layer=0,
                    volume=1.0
                ),
                ContainerBox(
                    box_type="edts",
                    children=[
                        ElstBox(
                            box_type="elst",
                            number_of_entries=1,
                            edit_list_table=[
                                EditList(
                                    track_duration=self.movie_header.duration,
                                    media_time=0,
                                    media_rate=1.0
                                )
                            ]
                        )
                    ]
                ),
                ContainerBox(
                    box_type="mdia",
                    children=[
                        MdhdBox(
                            box_type="mdhd",
                            creation_time=int(now),
                            modification_time=int(now),
                            time_scale=int(fps * 1000),
                            duration=len(data),
                            language=10766,
                        ),
                        HdlrBox(
                            box_type="hdlr",
                            component_type="mhlr",
                            component_subtype="tast",
                            component_name="TTTV".encode("ascii")
                        ),
                        ContainerBox(
                            box_type="minf",
                            children=[
                                TmhdBox(
                                    box_type="tmhd",
                                    balance=0
                                ),
                                ContainerBox(
                                    box_type="dinf",
                                    children=[
                                        DrefBox(
                                            box_type="dref",
                                            number_of_entries=1,
                                            data_references=[
                                                UrlBox(box_type="url")
                                            ]
                                        )
                                    ]
                                ),
                                sample_table
                            ]

                        )

                    ]
                )
            ]
        )
        pass


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


class MediaDataComponent(EvalComponent):
    def __init__(self, parsed: MdatBox, sample_table: SampleTableComponent, media_type):
        super().__init__(parsed)
        self.offset = parsed.begin_point
        self.media_type = media_type
        self.sample_table = sample_table
        data = parsed.body
        sample_i = 0
        next_sample_to_chunk_i = 0
        samples_per_chunk = 0
        self.data: list[ChunkData] = []
        for chunk_i, chunk_offset in enumerate(sample_table.chunk_offset.chunk_to_offset_table, start=1):

            sample_to_chunk_table = sample_table.sample_to_chunk.sample_to_chunk_table
            if next_sample_to_chunk_i < len(sample_to_chunk_table) \
                    and sample_to_chunk_table[next_sample_to_chunk_i].first_chunk == chunk_i:
                samples_per_chunk = sample_to_chunk_table[next_sample_to_chunk_i].samples_per_chunk
                next_sample_to_chunk_i += 1
            samples: list[SampleData] = []
            chunk_inside_offset = 0

            begin_time = self.get_time_of_sample(sample_i)
            for j in range(samples_per_chunk):
                sample_size = sample_table.sample_size.sample_size if sample_table.sample_size.sample_size != 0 else \
                    sample_table.sample_size.sample_size_table[sample_i]
                sample_start = (chunk_offset - self.offset) + chunk_inside_offset
                samples.append(SampleData(data[sample_start: sample_start + sample_size]))
                chunk_inside_offset += sample_size
                sample_i += 1

            end_time = self.get_time_of_sample(sample_i - 1)
            self.data.append(ChunkData(samples, self.media_type, begin_time=begin_time, end_time=end_time))
        for d in self.data:
            d.print()

    def get_time_of_sample(self, sample_i):
        table = self.sample_table.time_to_sample.time_to_sample_table
        t = 0
        sample_n = 0
        for td in table:
            for i in range(td.sample_count):

                if sample_n == sample_i:
                    return t
                t += td.sample_delta
                sample_n += 1


class SampleData:
    def __init__(self, data: bytes):
        self.data = data

    def print(self):
        print("-", len(self.data), end=",")

    def __len__(self):
        return len(self.data)


class ChunkData:
    def __init__(self, samples: list[SampleData], media_type: str, begin_time=0, end_time=0):
        self.samples = samples
        self.media_type = media_type
        self.begin_time = begin_time
        self.end_time = end_time

    def get_size(self):
        size = 0
        for sample in self.samples:
            size += len(sample)
        return size

    def print(self):
        print()
        print(f"Chunk - begin time{self.begin_time}, end_time{self.end_time}")

        for sample in self.samples:
            sample.print()

    def write(self, buffer: io.BytesIO):
        for sample in self.samples:
            buffer.write(sample.data)
