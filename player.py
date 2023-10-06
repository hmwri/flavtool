import os.path
import time

import numpy as np

from boxs.leaf import *
import composer
import parser
from components.components import *
import time
import concurrent.futures


class Player:
    def __init__(self, path):
        self.f = open(path, "rb")
        self.parsed = parser.Parser(path).parse(read_mdat_bytes=False)
        self.composer = composer.Composer(self.parsed, streaming=True)
        taste_track = self.composer.taste_track
        self.taste_media_data = self.composer.taste_media_data
        self.sample_table = taste_track.media.media_info.sample_table
        self.codec = self.sample_table.sample_description.sample_description_table[0].data_format
        self.time_scale = taste_track.media.header.time_scale
        self.t = 0
        self.frame_i = 0
        self.now_sample: StreamingSampleData = None
        self.all_samples = self.collect_samples(self.taste_media_data.data, self.sample_table)
        self.playing=True
        self.now_frame = None


    def read_int(self, n):
        return int.from_bytes(self.f.read(n), byteorder='big')

    def stop(self):
        self.playing = False

    def play(self):
        self.seek(self.t)
        self.playing = True
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
        executor.submit(self.play_loop)

    def play_loop(self):

        while self.playing:
            data, delta = self.next_frame()
            self.now_frame = data
            self.t += delta
            time.sleep(delta)
            print(data, delta)


    def collect_samples(self, chunks: list[ChunkData], sample_table: SampleTableComponent) -> list[StreamingSampleData]:
        result = []
        i = 0
        for c in chunks:
            for s in c.samples:
                result.append(s)
                i += 1

        table = sample_table.time_to_sample.time_to_sample_table
        t = 0
        sample_n = 0
        for td in table:
            for i in range(td.sample_count):

                result[sample_n].set_info(sample_n,t, td.sample_delta / self.time_scale,
                                          )
                t += td.sample_delta / self.time_scale
                sample_n += 1

        return result

    def seek(self, t):
        sample = self.get_sample(t)
        self.now_sample: StreamingSampleData = sample
        self.decode(sample)
        data_len = self.now_sample.data.shape[0]
        frame_duration = self.now_sample.delta / data_len
        res = t - self.now_sample.start_time
        frame_data = self.now_sample.get_frame_data(min(int(res / frame_duration), data_len - 1))
        print(frame_data)

    def next_frame(self):
        next_frame_data = self.now_sample.get_next_frame_data()
        if next_frame_data is not None:
            return next_frame_data, self.now_sample.delta
        else:
            self.now_sample = self.all_samples[self.now_sample.sample_i + 1]
            self.decode(self.now_sample)
            return self.now_sample.get_frame_data(0), self.now_sample.delta

    def decode(self, sample: StreamingSampleData) -> np.ndarray:

        self.f.seek(sample.start, os.SEEK_SET)
        if self.codec == "raw5":

            frame_in_samples = int(sample.length / 5)
            result = np.zeros((frame_in_samples, 5))
            for j in range(frame_in_samples):
                result[j] = np.array([self.read_int(1) for i in range(5)])
            sample.data = result
            return result
        else:
            raise AssertionError

    def get_sample(self, t):

        chunks = self.taste_media_data.data

        i = 0
        for c in chunks:
            end_sample = self.all_samples[i + len(c.samples) - 1]
            if end_sample.start_time + end_sample.delta >= t:
                for s in c.samples:
                    if t >= s.start_time:
                        return s
                    i += 1
            i += len(c.samples)
        return None
