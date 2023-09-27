from typing import BinaryIO
from datetime import datetime, timedelta
from boxs.leaf import *

containerNames = ["moov", "trak", "edts", "minf", "stbl", "acv1", "dinf", "mdia"]


class ContainerBox(Box):
    def __init__(self, box_type):
        super().__init__(box_type)
        self.children: list[Box] = []

    def __getitem__(self, item) -> Box:
        for child in self.children:
            if child.box_type == item:
                return child


    def parse(self, f: BinaryIO, body_size: int):
        begin_byte = f.tell()

        while f.tell() < begin_byte + body_size:
            child_box_type, child_box_size, child_body_size, is_extended = self.get_type_and_size(f)
            print(f.tell(), child_box_type, child_box_size, child_body_size)
            if child_box_type in containerNames:
                box = ContainerBox(child_box_type)
            elif child_box_type == "ftyp":
                box = FtypBox(child_box_type)
            elif child_box_type == "free":
                box = FreeBox(child_box_type)
            elif child_box_type == "mdat":
                box = MdatBox(child_box_type,is_extended)
            elif child_box_type == "mvhd":
                box = MvhdBox(child_box_type)
            elif child_box_type == "tkhd":
                box = TkhdBox(child_box_type)
            elif child_box_type == "mdhd":
                box = MdhdBox(child_box_type)
            elif child_box_type == "hdlr":
                box = HdlrBox(child_box_type)
            elif child_box_type == "vmhd":
                box = VmhdBox(child_box_type)
            elif child_box_type == "smhd":
                box = SmhdBox(child_box_type)
            else:
                box = UnknownBox(child_box_type)
            box.parse(f, child_body_size)

            self.children.append(box)

        return self

    def get_size(self) -> int:
        size = 0
        for child in self.children:
            size += child.get_size()
        return self.get_overall_size(size)

    def write(self, f: BinaryIO):
        if self.box_type != "root":
            size = self.get_size()
            box_type = self.box_type
            self.write_type_and_size(f, box_type, size)
        for child in self.children:
            child.write(f)

    @staticmethod
    def get_type_and_size(f: BinaryIO):
        box_size: int = int.from_bytes(f.read(4), byteorder='big')
        box_type: str = f.read(4).decode("ascii")
        body_size: int = box_size - 8
        extended = box_size == 1
        if extended:
            print("big")
            box_size = int.from_bytes(f.read(8), byteorder="big")
            body_size = box_size - 16
        return box_type, box_size, body_size, extended

    def print(self, depth):
        for d in range(depth):
            print("\t", end="")
        print(f"Container -  {self.box_type}")
        for child in self.children:
            child.print(depth + 1)
