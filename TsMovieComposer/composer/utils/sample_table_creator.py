from TsMovieComposer.analyzer.media_data import ChunkData
from TsMovieComposer.parser.boxs.container import ContainerBox
from TsMovieComposer.parser.boxs.leaf import *

class SampleTableCreator:
    """
    サンプルテーブルを作るクラス
    """
    def __init__(self, chunks: list[ChunkData], codec:str):
        """
        サンプルテーブルを作るクラス

        Parameters
        ----------
        chunks : list[ChunkData]
            対象のチャンクデータ
        codec : str
            コーデック
        """
        self.chunks = chunks
        self.codec = codec

    def __make_sample_to_chunk_table(self) -> list[SampleToChunk]:
        """
        SampleToChunkテーブル(どのサンプルがどのチャンクに属するか)を作成する

        Returns
        ----------
        sample_to_chunk_table : list[SampleToChunk]
            SampToChunk 構造体のリスト

        """
        sample_to_chunk_table: list[SampleToChunk] = []
        pre_sample_per_chunk = -1
        for i, c in enumerate(self.chunks, start=1):
            if len(c.samples) != pre_sample_per_chunk:
                sample_to_chunk_table.append(SampleToChunk(i, len(c.samples), c.sample_description))
                pre_sample_per_chunk = len(c.samples)
        return sample_to_chunk_table

    def __get_sample_size(self) -> tuple[int, list[int]]:
        """
        サンプルサイズを計算し、サンプルサイズテーブルを返す
        Returns
        -------
        sample_size: tuple[int, list[int]]
            すべて同じサイズなら、(サイズ、空配列), 異なるサイズなら(0、サイズの配列)を返します
        """
        sizes = [len(self.chunks[0][0].data)]
        first = True
        all_same = True
        for c in self.chunks:
            for s in c.samples:
                if not first:
                    size = len(s.data)
                    if size != sizes[-1]:
                        all_same =False
                        break
                    sizes.append(size)
                first = False

        if all_same:
            return sizes[0], []
        else:
            return 0, sizes


    def __make_time_to_sample_table(self) -> list[TimeToSample]:
        deltas = [self.chunks[0][0].delta]
        table : list[TimeToSample] = [
            TimeToSample(1, deltas[0])
        ]
        first = True
        for c in self.chunks:
            for s in c.samples:
                if not first:
                    delta = s.delta
                    if delta != table[-1].sample_delta :
                        table.append(TimeToSample(1, delta))
                    else:
                        table[-1].sample_count += 1
                    deltas.append(delta)
                first = False
        return table








    def make_sample_table(self) -> ContainerBox:
        """
        サンプルテーブルを作成する(Stcoの中身を除く)
        Returns
        -------
        sample_table : ContainerBox
            サンプルテーブル(Container Box-Stbl)

        """

        sample_to_chunk_table = self.__make_sample_to_chunk_table()
        sample_size, sample_size_table = self.__get_sample_size()
        time_to_sample = self.__make_time_to_sample_table()
        sample_table = ContainerBox(
            box_type="stbl",
            children=[
                StsdBox(
                    box_type="stsd",
                    number_of_entries=1,
                    sample_description_table=[
                        SampleDescription(
                            sample_description_size=None,
                            data_format=self.codec,
                            data_reference_index=1
                        )
                    ],
                ),
                SttsBox(
                    box_type="stts",
                    number_of_entries=len(time_to_sample),
                    time_to_sample_table=self.__make_time_to_sample_table()
                ),
                StscBox(
                    box_type="stsc",
                    number_of_entries=len(sample_to_chunk_table),
                    sample_to_chunk_table=sample_to_chunk_table
                ),
                StszBox(
                    box_type="stsz",
                    sample_size=sample_size,
                    number_of_entries=len(sample_size_table),
                    sample_size_table=sample_size_table
                ),
                StcoBox(
                    box_type="stco",
                    number_of_entries=len(self.chunks)
                )
            ]
        )
        return sample_table

