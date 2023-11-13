from typing import Literal

from TsMovieComposer.analyzer.components import *
from TsMovieComposer.analyzer.media_data import SampleData, MediaData, ChunkData
from TsMovieComposer.parser.boxs.container import ContainerBox
from TsMovieComposer.parser.boxs.leaf import *
import numpy as np
from TsMovieComposer.composer.utils.sample_table_creator import SampleTableCreator
from TsMovieComposer.composer.utils.track_box_creator import TrackBoxCreator
from TsMovieComposer.codec import get_encoder
from TsMovieComposer.analyzer import FlavMP4

media_types = Literal["tast", "soun", "vide", "scnt"]


class Composer:
    """
    Composer
        VideoとSoundがすでにあるmp4ファイルについて、味トラックと香りトラックを付け加える
    """
    @property
    def sample_tables(self) -> dict[media_types, SampleTableComponent | None] :
        sample_tables : dict[media_types, SampleTableComponent | None] = {}
        for k, v in self.flav_mp4.tracks.items():
            if v is None:
                sample_tables[k] = None
                continue
            sample_tables[k] = v.media.media_info.sample_table
        return sample_tables


    def __init__(self, flav_mp4:FlavMP4):
        """
        パースされたMp4の情報をもとに、トラック情報、サンプルデータ情報を構築
        Parameters
        ----------
        parsed_box : ContainerBox
            パースされたMP4データ
        streaming : bool
            strea

        """
        self.flav_mp4 : FlavMP4 = flav_mp4




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
        criteria_time_scale = self.flav_mp4.tracks[criteria_media_type].media.header.time_scale
        target_time_scales = [self.flav_mp4.tracks[media_type].media.header.time_scale for media_type in target_media_types]

        chunks: list[ChunkData] = []
        criteria_chunks: list[ChunkData] = self.flav_mp4.media_datas[criteria_media_type].data
        targets_chunks: list[list[ChunkData]] = [self.flav_mp4.media_datas[media_type].data for media_type in target_media_types]

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

    def __select_criteria(self, target_media_types: list[media_types]) -> tuple[media_types, list[media_types]]:
        priorities : list[media_types] = ["vide", "soun", "tast", "scnt"]
        for mt in priorities:
            if mt in target_media_types:
                criteria = mt
                others =  target_media_types.copy()
                others.remove(criteria)
                return criteria, others


    def compose(self, include_media_types : None |list[media_types] = None):
        if include_media_types is None:
            include_media_types = []
            for k, v in self.flav_mp4.tracks.items():
                if v is not None:
                    include_media_types.append(k)

        criteria_media_type, target_media_types = self.__select_criteria(include_media_types)
        chunks, offsets = self.__generate_interleave_chunks(criteria_media_type,target_media_types)

        # for c in chunks:
        #     c.print()

        buffer = io.BytesIO()
        for chunk in chunks:
            chunk.write(buffer)
        buffer.seek(0)
        self.flav_mp4.mdat.body = buffer.read()

        for cm in include_media_types:
            print(len(offsets[cm]))
            self.__create_dummy_stco(len(offsets[cm]), stco=self.sample_tables[cm].chunk_offset)

        mdat, mdat_offset = self.flav_mp4.parsed.get_mdat_offset()

        self.flav_mp4.mdat.begin_point = mdat_offset

        for cm in include_media_types:
            print(cm)
            self.sample_tables[cm].chunk_offset.chunk_to_offset_table = [co + mdat_offset for co in offsets[cm]]
        self.sample_tables["soun"].chunk_offset.print()
        self.flav_mp4.parsed.print()

    def set_track(self, media_type:media_types, track_component:TrackComponent):
        if self.flav_mp4.tracks[media_type] is not None:
            self.flav_mp4.parsed["moov"].children.remove(self.flav_mp4.tracks[media_type].parsed)
        self.flav_mp4.parsed["moov"].children.append(track_component.parsed)
        self.flav_mp4.tracks[media_type] = track_component

    def set_new_modal(self, media_type:media_types, track_component:TrackComponent, media_data:MediaData):
        self.set_track(media_type, track_component)
        self.flav_mp4.media_datas[media_type] = media_data


    def __create_dummy_stco(self, chunks_len: int, stco: StcoBox):
        if stco is None:
            return
        stco.number_of_entries = chunks_len
        stco.chunk_to_offset_table = []

    def __make_chunks(self, codec, data: np.ndarray, sample_delta) -> list[ChunkData]:
        encoder = get_encoder(codec)
        chunks = []
        sample_per_chunk = 50
        samples_in_chunks = 0
        t = 0
        now_chunk = ChunkData(samples=[], media_type="tast", begin_time=t,
                              end_time=t + sample_per_chunk * sample_delta)
        for frame_i in range(data.shape[0]):
            sample = SampleData(encoder(data[frame_i]))
            print(sample.data)
            now_chunk.samples.append(sample)
            samples_in_chunks += 1
            if samples_in_chunks == sample_per_chunk or frame_i == data.shape[0] - 1:
                samples_in_chunks = 0
                chunks.append(now_chunk)
                now_chunk = ChunkData(samples=[], media_type="tast", begin_time=t,
                                      end_time=t + sample_per_chunk * sample_delta)
            t += sample_delta
        return chunks

    def add_track(self, media_type: media_types, data: np.ndarray, fps: float, codec: str, replace=False):
        if not replace:
            if self.flav_mp4.tracks[media_type] is not None:
                print(f"Already track:{media_type} exists, If you want to replace, please set replace tag to true")
                return

        frame_n = data.shape[0]
        sample_delta = 1000
        chunks = self.__make_chunks(codec, data, sample_delta)

        for c in chunks:
            c.print()

        mov_time_scale = self.flav_mp4.mov_header.time_scale

        sample_table = SampleTableCreator(chunks, codec=codec, sample_delta=sample_delta).make_sample_table()
        track_box = TrackBoxCreator(
            track_duration=int(frame_n * mov_time_scale / fps),
            media_time_scale=int(fps * 1000),
            media_duration=frame_n * 1000,
            component_subtype=media_type,
            component_name="TTTV3",
            sample_table=sample_table
        ).create()
        self.set_track(media_type,TrackComponent(track_box))
        self.flav_mp4.media_datas[media_type] = MediaData(media_type=media_type, data=chunks)


    def write(self, path: str):
        self.compose()
        with open(path, "wb") as f:
            self.flav_mp4.parsed.write(f)
