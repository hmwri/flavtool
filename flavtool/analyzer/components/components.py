from flavtool.parser.boxs.container import ContainerBox
from flavtool.parser.boxs.leaf import *
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






