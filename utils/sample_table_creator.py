from components.components import *
from boxs.container import ContainerBox
from boxs.leaf import *
import numpy as np


class SampleTableCreator:
    def __init__(self, chunks: list[ChunkData], sample_delta, codec):
        self.chunks = chunks
        self.sample_delta = sample_delta
        self.codec = codec

    def make_sample_to_chunk_table(self):
        sample_to_chunk_table: list[SampleToChunk] = []
        pre_sample_per_chunk = -1
        for i, c in enumerate(self.chunks, start=1):
            if len(c.samples) != pre_sample_per_chunk:
                sample_to_chunk_table.append(SampleToChunk(i, len(c.samples), c.sample_description))
                pre_sample_per_chunk = len(c.samples)
        return sample_to_chunk_table

    def get_sample_size(self):
        sizes = []
        all_same = True
        for c in self.chunks:
            for s in c.samples:
                size = len(s.data)
                sizes.append(size)
                if all_same and size != sizes[-1]:
                    all_same = False
        if all_same:
            return sizes[0], []
        else:
            return 0, sizes


    # サンプルテーブルを作成(Stcoを除く StcoはCompose時に作成)
    def make_sample_table(self):
        sample_count = sum(len(c.samples) for c in self.chunks)
        sample_to_chunk_table = self.make_sample_to_chunk_table()
        sample_size, sample_size_table = self.get_sample_size()
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
                    number_of_entries=1,
                    time_to_sample_table=[
                        TimeToSample(
                            sample_count=sample_count,
                            sample_delta=self.sample_delta
                        )
                    ]
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

