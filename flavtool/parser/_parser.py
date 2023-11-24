import os
from flavtool.parser.boxs.container import ContainerBox
from typing import BinaryIO
import io
class Parser :
    def __init__(self, path:str, fp : BinaryIO|None = None):
        self.parsed_box = None
        self.path = path
        self.size = os.path.getsize(path)
        self.f = None
        if isinstance(fp, io.BufferedIOBase):
            self.f = fp

    def parse(self, read_mdat_bytes=True):
        if self.f is  None:
            with open(self.path, "rb") as f:
                self.parsed_box = ContainerBox("root").parse(f, self.size, read_mdat_bytes)
        else:
            self.parsed_box = ContainerBox("root").parse(self.f, self.size, read_mdat_bytes)
        return self.parsed_box

    def write(self, path:str):
        with open(path, "wb") as f:
            self.parsed_box.write(f)





