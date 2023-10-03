import io
from components.components import  *
from boxs.container import ContainerBox
from boxs.leaf import *
import numpy as np
from utils.sample_table_creator import SampleTableCreator
from utils.track_box_creator import TrackBoxCreator


class Composer:
    def __init__(self, parsed_box: ContainerBox):
        self.taste_track = None
        self.scent_track = None
        self.taste_media_data = None
        self.scent_media_data = None

        self.parsed = parsed_box
        box: ContainerBox
        for box in self.parsed["moov"].children:
            if box.box_type == "trak":
                subtype: str = box["mdia"]["hdlr"].component_subtype
                if subtype == "soun":
                    self.sound_track = TrackComponent(box)
                elif subtype == "vide":
                    self.video_track = TrackComponent(box)
                elif subtype == "tast":
                    self.taste_track = TrackComponent(box)
                elif subtype == "scnt":
                    self.scent_track = TrackComponent(box)

        self.video_sample_table = self.video_track.media.media_info.sample_table
        self.video_media_data = MediaData(
            self.parsed["mdat"],
            self.video_sample_table,
            "video"
        )
        self.movie_header: MvhdBox = self.parsed["moov"]["mvhd"]
        self.sound_sample_table = self.sound_track.media.media_info.sample_table
        self.sound_media_data = MediaData(
            self.parsed["mdat"],
            self.sound_sample_table,
            "sound"
        )

        if self.taste_track is not None:
            self.taste_sample_table = self.taste_track.media.media_info.sample_table
            self.taste_media_data = MediaData(
                self.parsed["mdat"],
                self.taste_sample_table,
                "tast"
            )

        if self.scent_track is not None:
            self.scent_sample_table = self.scent_track.media.media_info.sample_table
            self.scent_media_data = MediaData(
                self.parsed["mdat"],
                self.scent_sample_table,
                "scnt"
            )


        self.mdat: MdatBox = self.parsed["mdat"]


    def augment_track_to_video(self, track:TrackComponent, media_data:MediaData):
        video_sps = self.video_track.media.header.time_scale
        target_sps = track.media.header.time_scale

        chunks: list[ChunkData] = []
        video_chunks = self.video_media_data.data
        target_chunks = media_data.data

        video_chunk_offsets = []
        target_chunk_offsets = []
        target_i = 0
        offset = 0
        for video_chunk in video_chunks:
            # print(offset)
            video_chunk_offsets.append(offset)
            chunks.append(video_chunk)
            offset += video_chunk.get_size()
            while target_i < len(target_chunks) and target_chunks[
                target_i].begin_time / target_sps <= video_chunk.end_time / video_sps:
                target_chunk_offsets.append(offset)
                target_chunk = target_chunks[target_i]
                chunks.append(target_chunk)
                offset += target_chunk.get_size()
                target_i += 1
        while target_i < len(target_chunks):
            target_chunk_offsets.append(offset)
            chunks.append(target_chunks[target_i])
            offset += target_chunks[target_i].get_size()
            target_i += 1

        buffer = io.BytesIO()
        for chunk in chunks:
            chunk.write(buffer)
        buffer.seek(0)
        self.mdat.body = buffer.read()

        self.create_dummy_stco(len(video_chunks), stco=self.video_sample_table.chunk_offset)
        self.create_dummy_stco(len(target_chunks), stco=track.media.media_info.sample_table.chunk_offset)
        mdat, mdat_offset = self.parsed.get_mdat_offset()
        self.mdat.begin_point = mdat_offset
        self.video_sample_table.chunk_offset.chunk_to_offset_table = [vco + mdat_offset for vco in video_chunk_offsets]
        track.media.media_info.sample_table.chunk_offset.chunk_to_offset_table = [sco + mdat_offset for sco in target_chunk_offsets]

    def compose(self):

        self.augment_track_to_video(track=self.sound_track, media_data=self.sound_media_data)
        if self.taste_track is not None:
            self.augment_track_to_video(track=self.taste_track, media_data=self.taste_media_data)

        if self.scent_track is not None:
            self.augment_track_to_video(track=self.scent_track, media_data=self.scent_media_data)
        # time_scale
        # video_sps = self.video_track.media.header.time_scale
        # sound_sps = self.sound_track.media.header.time_scale
        #
        # chunks: list[ChunkData] = []
        # video_chunks = self.video_media_data.data
        # sound_chunks = self.sound_media_data.data
        #
        #
        # video_chunk_offsets = []
        # sound_chunk_offsets = []
        # sound_i = 0
        # offset = 0
        # for video_chunk in video_chunks:
        #     #print(offset)
        #     video_chunk_offsets.append(offset)
        #     chunks.append(video_chunk)
        #     offset += video_chunk.get_size()
        #     while sound_i < len(sound_chunks) and sound_chunks[
        #         sound_i].begin_time / sound_sps <= video_chunk.end_time / video_sps:
        #         sound_chunk_offsets.append(offset)
        #         sound_chunk = sound_chunks[sound_i]
        #         chunks.append(sound_chunk)
        #         offset += sound_chunk.get_size()
        #         sound_i += 1
        # while sound_i < len(sound_chunks):
        #     sound_chunk_offsets.append(offset)
        #     chunks.append(sound_chunks[sound_i])
        #     offset += sound_chunks[sound_i].get_size()
        #     sound_i += 1
        #
        # buffer = io.BytesIO()
        # for chunk in chunks:
        #     chunk.write(buffer)
        # buffer.seek(0)
        # self.mdat.body = buffer.read()
        #
        # self.create_dummy_stco(len(video_chunks), stco=self.video_sample_table.chunk_offset)
        # self.create_dummy_stco(len(sound_chunks), stco=self.sound_sample_table.chunk_offset)
        # mdat, mdat_offset = self.parsed.get_mdat_offset()
        # self.mdat.begin_point = mdat_offset
        # self.video_sample_table.chunk_offset.chunk_to_offset_table = [vco + mdat_offset for vco in video_chunk_offsets]
        # self.sound_sample_table.chunk_offset.chunk_to_offset_table = [sco + mdat_offset for sco in sound_chunk_offsets]
        # #print(self.sound_sample_table.chunk_offset)

    def create_dummy_stco(self, chunks_len: int, stco: StcoBox = None):
        if stco is None:
            return
        stco.number_of_entries = chunks_len
        stco.chunk_to_offset_table = []


    def make_chunks(self, codec, data:np.ndarray, sample_delta) -> list[ChunkData]:
        if codec == "raw5":
            chunks = []
            sample_per_chunk = 30
            samples_in_chunks = 0
            t = 0
            now_chunk = ChunkData(samples=[], media_type="tast", begin_time=t, end_time=t+sample_per_chunk*sample_delta)
            for frame_i in range(data.shape[0]):
                sample = SampleData(data[frame_i].tolist())
                now_chunk.samples.append(sample)
                samples_in_chunks += 1
                if samples_in_chunks == sample_per_chunk or frame_i == data.shape[0] - 1:
                    samples_in_chunks = 0
                    chunks.append(now_chunk)
                    now_chunk = ChunkData(samples=[], media_type="tast", begin_time=t, end_time=t+sample_per_chunk*sample_delta)
                t += sample_delta
            return chunks
        print("Unknown codec")
        return None

    def add_track(self, media_type:str, data: np.ndarray, fps: float, codec: str):
        if media_type=="tast" and self.taste_track is not None:
            print("already taste track exists!")
            return
        if media_type=="scnt" and self.scent_track is not None:
            print("already scent track exists!")
            return
        frame_n = data.shape[0]

        sample_delta = 1000
        chunks = self.make_chunks(codec,data, sample_delta)

        for c in chunks:
            c.print()

        sample_table = SampleTableCreator(chunks, codec=codec, sample_delta=sample_delta).make_sample_table()
        track_box = TrackBoxCreator(
            track_duration=frame_n * fps,
            media_time_scale=int(fps*1000),
            media_duration=frame_n*1000,
            component_subtype=media_type,
            component_name="TTTV3",
            sample_table= sample_table
        ).create()
        self.parsed["moov"].children.append(track_box)
        self.parsed.print()
        if media_type == "tast":
            self.taste_track = TrackComponent(track_box)
            self.taste_media_data = MediaData(media_type="tast", chunks=chunks)
        elif media_type == "scnt":
            self.scent_track = TrackComponent(track_box)
        else:
            raise AssertionError

    def write(self, path:str):
        with open(path, "wb") as f:
            self.parsed.write(f)




