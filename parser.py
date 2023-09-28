from typing import  *
import os
from boxs.container import ContainerBox

class Parser :
    def __init__(self, path):
        self.parsed_box = None
        self.path = path
        self.sound_track = None
        self.video_track = None

    def parse(self):
        with open(self.path, "rb") as f:
            size = os.path.getsize(self.path)
            print(size)
            self.parsed_box = ContainerBox("root").parse(f, size)
            self.parsed_box.print(0)

        for box in self.parsed_box["moov"].children:
            if box.box_type == "trak":
                if box["mdia"]["hdlr"].component_subtype == "soun":
                    self.sound_track = box
                else :
                    self.video_track = box

        return self.parsed_box

    def write(self, path:str):
        with open(path, "wb") as f:
            self.parsed_box.write(f)





