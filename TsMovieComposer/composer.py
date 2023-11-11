from typing import Literal

from TsMovieComposer.components.components import *
from TsMovieComposer.boxs.container import ContainerBox
from TsMovieComposer.boxs.leaf import *
import numpy as np
from TsMovieComposer.utils.sample_table_creator import SampleTableCreator
from TsMovieComposer.utils.track_box_creator import TrackBoxCreator
from TsMovieComposer.logger import logger

media_types = Literal["tast", "soun", "vide", "scnt"]


class Composer:
    """
    Composer
        VideoとSoundがすでにあるmp4ファイルについて、味トラックと香りトラックを付け加える
    """

    def __init__(self, parsed_box: ContainerBox, streaming=False):
        """
        パースされたMp4の情報をもとに、トラック情報、サンプルデータ情報を構築
        Parameters
        ----------
        parsed_box : ContainerBox
            パースされたMP4データ
        streaming : bool
            strea
        """

        self.tracks: dict[media_types, TrackComponent | None] = {
            "tast": None,
            "soun": None,
            "vide": None,
            "scnt": None,
        }

        self.sample_tables: dict[media_types, SampleTableComponent | None] = {
            "tast": None,
            "soun": None,
            "vide": None,
            "scnt": None,
        }

        self.media_datas: dict[media_types, MediaData | None] = {
            "tast": None,
            "soun": None,
            "vide": None,
            "scnt": None,
        }

        self.taste_track: None | TrackComponent = None
        self.scent_track: None | TrackComponent = None
        self.taste_media_data: None | MediaData = None
        self.scent_media_data: None | MediaData = None

        self.parsed: ContainerBox = parsed_box

        self.mdat = self.parsed["mdat"]
        if not isinstance(self.mdat, MdatBox):
            raise Exception("mdat parse error")

        for box in self.parsed["moov"].children:
            if box.box_type == "trak":
                handler_box = box["mdia"]["hdlr"]
                if not isinstance(handler_box, HdlrBox):
                    logger.error("handler box parse error, this track will be ignored. ")
                    continue
                subtype: str = handler_box.component_subtype
                if subtype not in subtype:
                    logger.warning(f"{subtype} is not supported media type, so it will be ignored.")
                    continue

                subtype: media_types
                self.tracks[subtype] = TrackComponent(box)
                self.sample_tables[subtype] = self.tracks[subtype].media.media_info.sample_table
                self.media_datas[subtype] = MediaData(
                    self.mdat,
                    self.sample_tables[subtype],
                    subtype,
                    streaming=streaming
                )
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
            self.mdat,
            self.video_sample_table,
            "video",
            streaming=streaming
        )

        self.movie_header = self.parsed["moov"]["mvhd"]
        if not isinstance(self.movie_header, MvhdBox):
            logger.error("mdat box parse error")
        self.sound_sample_table = self.sound_track.media.media_info.sample_table
        self.sound_media_data = MediaData(
            self.mdat,
            self.sound_sample_table,
            "sound",
            streaming=streaming
        )

        if self.taste_track is not None:
            self.taste_sample_table = self.taste_track.media.media_info.sample_table
            self.taste_media_data = MediaData(
                self.mdat,
                self.taste_sample_table,
                "tast",
                streaming=streaming
            )

        if self.scent_track is not None:
            self.scent_sample_table = self.scent_track.media.media_info.sample_table
            self.scent_media_data = MediaData(
                self.mdat,
                self.scent_sample_table,
                "scnt",
                streaming=streaming
            )

    def __generate_interleave_chunks(self, criteria_media_type: media_types, target_media_types: list[media_types]) -> \
            tuple[list[ChunkData], dict[media_types, list[int]]]:
        """
        各メディアデータから、指定メディアタイプを基準とした適切なChunkリストとオフセットを作成
        Parameters
        ----------
        criteria_media_type
            基準となるメディアタイプ
        target_media_types
            対象となるメディアタイプ
        Returns
        -------
        ChunkData list and Offset Dictionary

        """
        track_n = len(target_media_types)
        criteria_time_scale = self.tracks[criteria_media_type].media.header.time_scale
        target_time_scales = [self.tracks[media_type].media.header.time_scale for media_type in target_media_types]

        chunks: list[ChunkData] = []
        criteria_chunks: list[ChunkData] = self.media_datas[criteria_media_type].data
        targets_chunks: list[list[ChunkData]] = [self.media_datas[media_type].data for media_type in target_media_types]

        criteria_chunk_offsets = []
        targets_chunk_offsets = [[] for _ in range(track_n)]
        targets_i = [0 for _ in range(track_n)]
        offset = 0
        for criteria_chunk in criteria_chunks:
            # print(offset)
            criteria_chunk_offsets.append(offset)
            chunks.append(criteria_chunk)
            offset += criteria_chunk.get_size()
            for track_i in range(track_n):
                target_chunks = targets_chunks[track_i]
                target_sps = target_time_scales[track_i]
                target_chunk_offsets = targets_chunk_offsets[track_i]
                while targets_i[track_i] < len(target_chunks) and target_chunks[
                    targets_i[track_i]].begin_time / target_sps <= criteria_chunk.end_time / criteria_time_scale:
                    target_chunk_offsets.append(offset)
                    target_chunk = target_chunks[targets_i[track_i]]
                    chunks.append(target_chunk)
                    offset += target_chunk.get_size()
                    targets_i[track_i] += 1
        for track_i in range(track_n):
            target_chunks = targets_chunks[track_i]
            target_chunk_offsets = targets_chunk_offsets[track_i]
            while targets_i[track_i] < len(target_chunks):
                target_chunk_offsets.append(offset)
                chunks.append(target_chunks[targets_i[track_i]])
                offset += target_chunks[targets_i[track_i]].get_size()
                targets_i[track_i] += 1
        result_offset: dict[media_types, list[int]] = {criteria_media_type: criteria_chunk_offsets}
        for i, tm in enumerate(target_media_types):
            result_offset[tm] = targets_chunk_offsets[i]
        return chunks, result_offset

    def augment_track_to_video(self, compose_media_types: list[media_types]):

        compose_media_types.remove("vide")
        chunks, offsets = self.__generate_interleave_chunks("vide", compose_media_types)

        # track_n = len(target_tracks)
        # criteria_time_scale = self.video_track.media.header.time_scale
        # target_time_scales = [t.media.header.time_scale for t in target_tracks]
        #
        # chunks: list[ChunkData] = []
        # criteria_chunks = self.video_media_data.data
        # targets_chunks = [media_data.data for media_data in target_media_datas]
        #
        # criteria_chunk_offsets = []
        # targets_chunk_offsets = [[] for _ in range(track_n)]
        # targets_i = [0 for _ in range(track_n)]
        # offset = 0
        # for video_chunk in criteria_chunks:
        #     # print(offset)
        #     criteria_chunk_offsets.append(offset)
        #     chunks.append(video_chunk)
        #     offset += video_chunk.get_size()
        #     for track_i in range(track_n):
        #         target_chunks = targets_chunks[track_i]
        #         target_sps = target_time_scales[track_i]
        #         target_chunk_offsets = targets_chunk_offsets[track_i]
        #         while targets_i[track_i] < len(target_chunks) and target_chunks[
        #             targets_i[track_i]].begin_time / target_sps <= video_chunk.end_time / criteria_time_scale:
        #             target_chunk_offsets.append(offset)
        #             target_chunk = target_chunks[targets_i[track_i]]
        #             chunks.append(target_chunk)
        #             offset += target_chunk.get_size()
        #             targets_i[track_i] += 1
        # for track_i in range(track_n):
        #     target_chunks = targets_chunks[track_i]
        #     target_chunk_offsets = targets_chunk_offsets[track_i]
        #     while targets_i[track_i] < len(target_chunks):
        #         target_chunk_offsets.append(offset)
        #         chunks.append(target_chunks[targets_i[track_i]])
        #         offset += target_chunks[targets_i[track_i]].get_size()
        #         targets_i[track_i] += 1

        for c in chunks:
            c.print()

        buffer = io.BytesIO()
        for chunk in chunks:
            chunk.write(buffer)
        buffer.seek(0)
        self.mdat.body = buffer.read()

        print(compose_media_types)
        for cm in compose_media_types:
            print(offsets)
            print(len(offsets[cm]))
            self.create_dummy_stco(len(offsets[cm]), stco=self.sample_tables[cm].chunk_offset)

        # self.create_dummy_stco(len(criteria_chunk_offsets), stco=self.video_sample_table.chunk_offset)
        # for track_i in range(track_n):
        #     self.create_dummy_stco(len(targets_chunk_offsets[track_i]),
        #                            stco=compose_media_types[track_i].media.media_info.sample_table.chunk_offset)

        mdat, mdat_offset = self.parsed.get_mdat_offset()

        self.mdat.begin_point = mdat_offset

        for cm in compose_media_types:
            self.sample_tables[cm].chunk_offset.chunk_to_offset_table = [co + mdat_offset for co in offsets[cm]]

        # self.video_sample_table.chunk_offset.chunk_to_offset_table = [vco + mdat_offset for vco in
        #                                                               criteria_chunk_offsets]
        # for track_i in range(track_n):
        #     target_tracks[track_i].media.media_info.sample_table.chunk_offset.chunk_to_offset_table = [sco + mdat_offset
        #                                                                                                for sco in
        #                                                                                                targets_chunk_offsets[
        #                                                                                                    track_i]]

    def compose(self):
        compose_media_type = []
        for k, v in self.tracks.items():
            if v is not None:
                compose_media_type.append(k)

        tracks = [self.sound_track]
        media_datas = [self.sound_media_data]

        if self.taste_track is not None:
            tracks.append(self.taste_track)
            media_datas.append(self.taste_media_data)

        if self.scent_track is not None:
            tracks.append(self.scent_track)
            media_datas.append(self.scent_media_data)
        print(compose_media_type)
        self.augment_track_to_video(compose_media_type)
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

    def create_dummy_stco(self, chunks_len: int, stco: StcoBox):
        if stco is None:
            return
        stco.number_of_entries = chunks_len
        stco.chunk_to_offset_table = []

    def make_chunks(self, codec, data: np.ndarray, sample_delta) -> list[ChunkData]:
        if codec == "raw5":
            chunks = []
            sample_per_chunk = 50
            samples_in_chunks = 0
            t = 0
            now_chunk = ChunkData(samples=[], media_type="tast", begin_time=t,
                                  end_time=t + sample_per_chunk * sample_delta)
            for frame_i in range(data.shape[0]):
                sample = SampleData(bytes(data[frame_i].tolist()))
                now_chunk.samples.append(sample)
                samples_in_chunks += 1
                if samples_in_chunks == sample_per_chunk or frame_i == data.shape[0] - 1:
                    samples_in_chunks = 0
                    chunks.append(now_chunk)
                    now_chunk = ChunkData(samples=[], media_type="tast", begin_time=t,
                                          end_time=t + sample_per_chunk * sample_delta)
                t += sample_delta
            return chunks
        print("Unknown codec")
        return None

    def add_track(self, media_type: str, data: np.ndarray, fps: float, codec: str):
        if media_type == "tast" and self.taste_track is not None:
            print("already taste track exists!")
            return
        if media_type == "scnt" and self.scent_track is not None:
            print("already scent track exists!")
            return
        frame_n = data.shape[0]

        sample_delta = 1000
        chunks = self.make_chunks(codec, data, sample_delta)

        for c in chunks:
            c.print()

        sample_table = SampleTableCreator(chunks, codec=codec, sample_delta=sample_delta).make_sample_table()
        track_box = TrackBoxCreator(
            track_duration=frame_n * fps,
            media_time_scale=int(fps * 1000),
            media_duration=frame_n * 1000,
            component_subtype=media_type,
            component_name="TTTV3",
            sample_table=sample_table
        ).create()
        self.parsed["moov"].children.append(track_box)
        self.parsed.print()
        if media_type == "tast":
            self.taste_track = TrackComponent(track_box)
            self.taste_media_data = MediaData(media_type="tast", data=chunks)
        elif media_type == "scnt":
            self.scent_track = TrackComponent(track_box)
            self.scent_media_data = MediaData(media_type="scnt", data=chunks)
        else:
            raise AssertionError

    def write(self, path: str):
        with open(path, "wb") as f:
            self.parsed.write(f)
