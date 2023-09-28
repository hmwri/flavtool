from typing import BinaryIO
from datetime import datetime, timedelta
from boxs.box import Box, Mp4Component

epoch_1904 = datetime(1904, 1, 1)


class LeafBox(Box):

    def parse(self, f: BinaryIO, body_size: int):
        raise NotImplemented

    def print(self, depth=0):
        raise NotImplemented

    def write(self, f: BinaryIO):
        raise NotImplemented

    def get_size(self) -> int:
        raise NotImplementedError


class UnknownBox(LeafBox):

    def __init__(self, box_type: str):
        super().__init__(box_type)
        self.body_data = b''
        self.box_type = box_type

    def parse(self, f: BinaryIO, body_size: int):
        print("parse: ", body_size)
        self.body_data = f.read(body_size)
        return self

    def print(self, depth=0):
        for d in range(depth):
            print("\t", end="")
        print(f"Unknown - {self.box_type}")

    def write(self, f: BinaryIO):
        self.write_type_and_size(f, self.box_type, self.get_size())
        f.write(self.body_data)

    def get_size(self) -> int:
        return self.get_overall_size(len(self.body_data))


class FtypBox(LeafBox):

    def __init__(self, box_type: str):
        super().__init__(box_type)
        self.major_brand: str = ""
        self.minor_version: bytes = b''
        self.compatible_brands: list[str] = []

    def parse(self, f: BinaryIO, body_size: int):
        self.major_brand = self.read_ascii(f, 4)
        self.minor_version = f.read(4)
        offset = 8
        while body_size - offset > 0:
            self.compatible_brands.append(str(self.read_ascii(f, 4)))
            offset += 4
        return self

    def write(self, f: BinaryIO):
        self.write_type_and_size(f, "ftyp", self.get_size())
        self.write_ascii(f, self.major_brand)
        f.write(self.minor_version)
        for brand in self.compatible_brands:
            self.write_ascii(f, brand)

    def get_size(self) -> int:
        return self.get_overall_size(4 + 4 + len(self.compatible_brands) * 4)

    def print(self, depth=0):
        self.print_with_indent("ftyp", depth)
        self.print_with_indent(f" - major_brand:{self.major_brand}", depth)
        self.print_with_indent(f" - minor_version:{self.minor_version}", depth)
        self.print_with_indent(f" - compatible_brands:{self.compatible_brands}", depth)


class FreeBox(LeafBox):
    def __init__(self, box_type: str):
        super().__init__(box_type)
        self.space: bytes = b''

    def parse(self, f: BinaryIO, body_size: int):
        self.space = f.read(body_size)
        return self

    def print(self, depth=0):
        self.print_with_indent("free", depth)
        self.print_with_indent(f" - space {self.space}", depth)

    def write(self, f: BinaryIO):
        self.write_type_and_size(f, "free", self.get_size())
        f.write(self.space)

    def get_size(self) -> int:
        return self.get_overall_size(len(self.space))


class MdatBox(LeafBox):
    def __init__(self, box_type: str, is_extended: bool):
        super().__init__(box_type)
        self.body: bytes = b''
        self.is_size_extended = is_extended

    def parse(self, f: BinaryIO, body_size: int):
        self.body = f.read(body_size)
        return self

    def print(self, depth=0):
        self.print_with_indent("free", depth)
        self.print_with_indent(f" - body {self.body[:10]}", depth)

    def write(self, f: BinaryIO):
        self.write_type_and_size(f, "mdat", self.get_size(), force_extended=self.is_size_extended)
        f.write(self.body)

    def get_size(self) -> int:
        return self.get_overall_size(len(self.body) + (8 if self.is_size_extended else 0))


class MvhdBox(LeafBox):
    def __init__(self, box_type: str):
        super().__init__(box_type)
        self.version: bytes = b''
        self.flags: bytes = b''
        self.creation_time: int = 0
        self.modification_time: int = 0
        self.time_scale: int = 0
        self.duration: int = 0
        self.preferred_rate: float = 0
        self.preferred_volume: float = 0
        self.reserved = b''
        self.matrix = b''
        self.predefines = b''
        self.next_track_id = b''

    def parse(self, f: BinaryIO, body_size: int):
        begin = f.tell()
        self.version = f.read(1)
        self.flags = f.read(3)
        self.creation_time = self.read_int(f, 4)
        self.modification_time = self.read_int(f, 4)
        self.time_scale = self.read_int(f, 4)
        self.duration = self.read_int(f, 4)
        self.preferred_rate = self.read_fixed_float32(f)
        self.preferred_volume = self.read_fixed_float16(f)
        self.reserved = f.read(10)
        self.matrix = f.read(36)
        offset = f.tell() - begin
        self.predefines = f.read(body_size - 4 - offset)
        self.next_track_id = f.read(4)
        return self

    def print(self, depth=0):
        self.print_with_indent("mvhd", depth)
        depth += 1  # Increase the depth for nested printing
        self.print_with_indent(f" - version: {self.version.hex()}", depth)
        self.print_with_indent(f" - flags: {self.flags.hex()}", depth)

        # 1904年1月1日からの経過時間をdatetimeオブジェクトに変換して出力
        creation_date = epoch_1904 + timedelta(seconds=self.creation_time)
        self.print_with_indent(f" - creation_time: {creation_date}", depth)

        modification_date = epoch_1904 + timedelta(seconds=self.modification_time)
        self.print_with_indent(f" - modification_time: {modification_date}", depth)

        self.print_with_indent(f" - time_scale: {self.time_scale}", depth)
        self.print_with_indent(f" - duration: {self.duration}", depth)
        self.print_with_indent(f" - preferred_rate: {self.preferred_rate}", depth)
        self.print_with_indent(f" - preferred_volume: {self.preferred_volume}", depth)
        self.print_with_indent(f" - reserved: {self.reserved.hex()}", depth)
        self.print_with_indent(f" - matrix: {self.matrix.hex()}", depth)
        self.print_with_indent(f" - predefines: {self.predefines.hex()}", depth)
        self.print_with_indent(f" - next_track_id: {self.next_track_id.hex()}", depth)

    def write(self, f: BinaryIO):
        self.write_type_and_size(f, "mvhd", self.get_size())

        f.write(self.version)
        f.write(self.flags)
        self.write_int(f, self.creation_time)
        self.write_int(f, self.modification_time)
        self.write_int(f, self.time_scale)
        self.write_int(f, self.duration)

        self.write_fixed_float32(f, self.preferred_rate)
        self.write_fixed_float16(f, self.preferred_volume)

        f.write(self.reserved)
        f.write(self.matrix)
        f.write(self.predefines)
        f.write(self.next_track_id)

    def get_size(self) -> int:
        return self.get_overall_size(1 + 3 + 4 * 4 + 4 + 2 + 10 + 36 + 4 + len(self.predefines))


class TkhdBox(LeafBox):

    def __init__(self, box_type: str):
        super().__init__(box_type)
        self.version: bytes = b''
        self.flags: bytes = b''
        self.creation_time: int = 0
        self.modification_time: int = 0
        self.track_id: int = 0
        self.reserved1 = b''
        self.duration: int = 0
        self.reserved2 = b''
        self.layer: int = 0
        self.alternative_group: bytes = b''
        self.volume: float = 0
        self.reserved3 = b''
        self.matrix = b''
        self.track_width: float = 0
        self.track_height: float = 0

    def parse(self, f: BinaryIO, body_size: int):
        self.version = f.read(1)
        self.flags = f.read(3)
        self.creation_time = self.read_int(f, 4)
        self.modification_time = self.read_int(f, 4)
        self.track_id = self.read_int(f, 4)
        self.reserved1 = f.read(4)
        self.duration = self.read_int(f, 4)
        self.reserved2 = f.read(8)
        self.layer = self.read_int(f, 2)
        self.alternative_group = f.read(2)
        self.volume = self.read_fixed_float16(f)
        self.reserved3 = f.read(2)
        self.matrix = f.read(36)
        self.track_width = self.read_fixed_float32(f)
        self.track_height = self.read_fixed_float32(f)
        return self

    def print(self, depth=0):
        self.print_with_indent("tkhd", depth)
        depth += 1
        self.print_with_indent(f" - version: {self.version.hex()}", depth)
        self.print_with_indent(f" - flags: {self.flags.hex()}", depth)

        # 1904年1月1日からの経過時間をdatetimeオブジェクトに変換して出力
        creation_date = epoch_1904 + timedelta(seconds=self.creation_time)
        self.print_with_indent(f" - creation_time: {creation_date}", depth)

        modification_date = epoch_1904 + timedelta(seconds=self.modification_time)
        self.print_with_indent(f" - modification_time: {modification_date}", depth)

        self.print_with_indent(f" - track_id: {self.track_id}", depth)
        self.print_with_indent(f" - reserved1: {self.reserved1.hex()}", depth)
        self.print_with_indent(f" - duration: {self.duration}", depth)
        self.print_with_indent(f" - reserved2: {self.reserved2.hex()}", depth)
        self.print_with_indent(f" - alternative_group: {self.alternative_group.hex()}", depth)
        self.print_with_indent(f" - volume: {self.volume}", depth)
        self.print_with_indent(f" - reserved3: {self.reserved3.hex()}", depth)
        self.print_with_indent(f" - matrix: {self.matrix.hex()}", depth)
        self.print_with_indent(f" - track_width: {self.track_width}", depth)
        self.print_with_indent(f" - track_height: {self.track_height}", depth)

    def write(self, f: BinaryIO):
        self.write_type_and_size(f, "tkhd", self.get_size())

        f.write(self.version)
        f.write(self.flags)
        self.write_int(f, self.creation_time)
        self.write_int(f, self.modification_time)
        self.write_int(f, self.track_id)
        f.write(self.reserved1)
        self.write_int(f, self.duration)
        f.write(self.reserved2)
        self.write_int(f, self.layer, length=2)
        f.write(self.alternative_group)
        self.write_fixed_float16(f, self.volume)
        f.write(self.reserved3)
        f.write(self.matrix)
        self.write_fixed_float32(f, self.track_width)
        self.write_fixed_float32(f, self.track_height)

    def get_size(self) -> int:
        return self.get_overall_size(1 + 3 + 4 * 5 + 8 + 2 * 4 + 36 + 8)


class MdhdBox(LeafBox):
    def __init__(self, box_type: str):
        super().__init__(box_type)
        self.version: bytes = b''
        self.flags: bytes = b''
        self.creation_time: int = 0
        self.modification_time: int = 0
        self.time_scale: int = 0
        self.duration: int = 0
        self.language: int = 0
        self.predefines = b''

    def parse(self, f: BinaryIO, body_size: int):
        begin = f.tell()
        self.version = f.read(1)
        self.flags = f.read(3)
        self.creation_time = self.read_int(f, 4)
        self.modification_time = self.read_int(f, 4)
        self.time_scale = self.read_int(f, 4)
        self.duration = self.read_int(f, 4)
        self.language = self.read_int(f, 2)
        self.predefines = f.read(body_size - (f.tell() - begin))
        return self

    def print(self, depth=0):
        self.print_with_indent("mdhd", depth)
        depth += 1  # Increase the depth for nested printing
        self.print_with_indent(f" - version: {self.version.hex()}", depth)
        self.print_with_indent(f" - flags: {self.flags.hex()}", depth)

        # 1904年1月1日からの経過時間をdatetimeオブジェクトに変換して出力
        creation_date = epoch_1904 + timedelta(seconds=self.creation_time)
        self.print_with_indent(f" - creation_time: {creation_date}", depth)

        modification_date = epoch_1904 + timedelta(seconds=self.modification_time)
        self.print_with_indent(f" - modification_time: {modification_date}", depth)

        self.print_with_indent(f" - time_scale: {self.time_scale}", depth)
        self.print_with_indent(f" - duration: {self.duration}", depth)
        self.print_with_indent(f" - language: {self.language}", depth)
        self.print_with_indent(f" - predefines: {self.predefines.hex()}", depth)

    def write(self, f: BinaryIO):
        self.write_type_and_size(f, "mdhd", self.get_size())
        f.write(self.version)
        f.write(self.flags)
        self.write_int(f, self.creation_time)
        self.write_int(f, self.modification_time)
        self.write_int(f, self.time_scale)
        self.write_int(f, self.duration)
        self.write_int(f, self.language, length=2)
        f.write(self.predefines)

    def get_size(self) -> int:
        return self.get_overall_size(1 + 3 + 4 * 4 + 2 + len(self.predefines))


class HdlrBox(LeafBox):
    def __init__(self, box_type: str):
        super().__init__(box_type)
        self.version: bytes = b''
        self.flags: bytes = b''
        self.component_type: str = ""
        self.component_subtype: str = ""
        self.component_name: bytes = b''

    def parse(self, f: BinaryIO, body_size: int):
        begin = f.tell()
        self.version = f.read(1)
        self.flags = f.read(3)
        self.component_type = self.read_ascii(f, 4)
        self.component_subtype = self.read_ascii(f, 4)
        self.component_name = f.read(body_size - (f.tell() - begin))
        return self

    def print(self, depth=0):
        self.print_with_indent("hdlr", depth)
        depth += 1  # Increase the depth for nested printing
        self.print_with_indent(f" - version: {self.version.hex()}", depth)
        self.print_with_indent(f" - flags: {self.flags.hex()}", depth)
        self.print_with_indent(f" - componentType: {self.component_type}", depth)
        self.print_with_indent(f" - componentSubtype: {self.component_subtype}", depth)
        self.print_with_indent(f" - componentName: {self.component_name.decode('ascii')}", depth)

    def write(self, f: BinaryIO):
        self.write_type_and_size(f, "hdlr", self.get_size())
        f.write(self.version)
        f.write(self.flags)
        self.write_ascii(f, self.component_type)
        self.write_ascii(f, self.component_subtype)
        f.write(self.component_name)

    def get_size(self) -> int:
        return self.get_overall_size(1 + 3 + 4 * 2 + len(self.component_name))


class VmhdBox(LeafBox):
    def __init__(self, box_type: str):
        super().__init__(box_type)
        self.version: bytes = b''
        self.flags: bytes = b''
        self.graphics_mode: int = 0
        self.opcolor: list[int] = []

    def parse(self, f: BinaryIO, body_size: int):
        self.version = f.read(1)
        self.flags = f.read(3)
        self.graphics_mode = self.read_int(f, 2)
        self.opcolor = [self.read_int(f, 2), self.read_int(f, 2), self.read_int(f, 2)]
        return self

    def print(self, depth=0):
        self.print_with_indent("vmhd", depth)
        depth += 1  # Increase the depth for nested printing
        self.print_with_indent(f" - version: {self.version.hex()}", depth)
        self.print_with_indent(f" - flags: {self.flags.hex()}", depth)
        self.print_with_indent(f" - graphics_mode: {self.graphics_mode}", depth)
        self.print_with_indent(f" - opcolor: {self.opcolor}", depth)

    def write(self, f: BinaryIO):
        self.write_type_and_size(f, "vmhd", self.get_size())
        f.write(self.version)
        f.write(self.flags)
        self.write_int(f, self.graphics_mode, 2)
        for i in range(3):
            self.write_int(f, self.opcolor[i], 2)

    def get_size(self) -> int:
        return self.get_overall_size(1 + 3 + 2 * 4)


class SmhdBox(LeafBox):
    def __init__(self, box_type: str):
        super().__init__(box_type)
        self.version: bytes = b''
        self.flags: bytes = b''
        self.balance: int = 0
        self.reserved: bytes = b''

    def parse(self, f: BinaryIO, body_size: int):
        self.version = f.read(1)
        self.flags = f.read(3)
        self.balance = self.read_int(f, 2)
        self.reserved = f.read(2)
        return self

    def print(self, depth=0):
        self.print_with_indent("smhd", depth)
        depth += 1  # Increase the depth for nested printing
        self.print_with_indent(f" - version: {self.version.hex()}", depth)
        self.print_with_indent(f" - flags: {self.flags.hex()}", depth)
        self.print_with_indent(f" - balance: {self.balance}", depth)
        self.print_with_indent(f" - reserved: {self.reserved}", depth)

    def write(self, f: BinaryIO):
        self.write_type_and_size(f, "smhd", self.get_size())
        f.write(self.version)
        f.write(self.flags)
        self.write_int(f, self.balance, 2)
        f.write(self.reserved)

    def get_size(self) -> int:
        return self.get_overall_size(1 + 3 + 2 * 2)


class DrefBox(LeafBox):
    def __init__(self, box_type: str):
        super().__init__(box_type)
        self.version: bytes = b''
        self.flags: bytes = b''
        self.number_of_entries: int = 0
        self.data_references: list[UrlBox] = []

    def parse(self, f: BinaryIO, body_size: int):
        self.version = f.read(1)
        self.flags = f.read(3)
        self.number_of_entries = self.read_int(f, 4)
        for i in range(self.number_of_entries):
            child_box_type, child_box_size, child_body_size, is_extended = self.get_type_and_size(f)
            self.data_references.append(UrlBox(child_box_type).parse(f, child_body_size))
        return self

    def print(self, depth=0):
        self.print_with_indent("dref", depth)
        depth += 1  # Increase the depth for nested printing
        self.print_with_indent(f" - version: {self.version.hex()}", depth)
        self.print_with_indent(f" - flags: {self.flags.hex()}", depth)
        self.print_with_indent(f" - number of entries: {self.number_of_entries}", depth)
        self.print_with_indent(f" - refs:", depth)
        for ref in self.data_references:
            ref.print(depth + 1)

    def write(self, f: BinaryIO):
        self.write_type_and_size(f, "dref", self.get_size())
        f.write(self.version)
        f.write(self.flags)
        self.write_int(f, self.number_of_entries)
        for ref in self.data_references:
            ref.write(f)

    def get_size(self) -> int:
        url_all_size = 0
        for ref in self.data_references:
            url_all_size += ref.get_size()
        return self.get_overall_size(1 + 3 + 4 + url_all_size)


class UrlBox(LeafBox):
    def __init__(self, box_type: str):
        super().__init__(box_type)
        self.version: bytes = b''
        self.flags: bytes = b''
        self.data: bytes = b''

    def parse(self, f: BinaryIO, body_size: int):
        self.version = f.read(1)
        self.flags = f.read(3)
        self.data = f.read(body_size - 4)
        return self

    def print(self, depth=0):
        self.print_with_indent(self.box_type, depth)
        depth += 1  # Increase the depth for nested printing
        self.print_with_indent(f" - version: {self.version.hex()}", depth)
        self.print_with_indent(f" - flags: {self.flags.hex()}", depth)
        self.print_with_indent(f" - data: {self.data.hex()}", depth)

    def write(self, f: BinaryIO):
        self.write_type_and_size(f, self.box_type, self.get_size())
        f.write(self.version)
        f.write(self.flags)
        f.write(self.data)

    def get_size(self) -> int:
        return self.get_overall_size(1 + 3 + len(self.data))


class StsdBox(LeafBox):
    def __init__(self, box_type: str):
        super().__init__(box_type)
        self.version: bytes = b''
        self.flags: bytes = b''
        self.number_of_entries: int = 0
        self.sample_description_table: list[SampleDescription] = []

    def parse(self, f: BinaryIO, body_size: int):
        self.version = f.read(1)
        self.flags = f.read(3)
        self.number_of_entries = self.read_int(f, 4)
        for i in range(self.number_of_entries):
            self.sample_description_table.append(SampleDescription().parse(f))
        return self

    def print(self, depth=0):
        self.print_with_indent("stsd", depth)
        depth += 1  # Increase the depth for nested printing
        self.print_with_indent(f" - version: {self.version.hex()}", depth)
        self.print_with_indent(f" - flags: {self.flags.hex()}", depth)
        self.print_with_indent(f" - number of entries: {self.number_of_entries}", depth)
        self.print_with_indent(f" - sample descriptions:", depth)
        for sample_description in self.sample_description_table:
            sample_description.print(depth + 1)

    def write(self, f: BinaryIO):
        self.write_type_and_size(f, "stsd", self.get_size())
        f.write(self.version)
        f.write(self.flags)
        self.write_int(f, self.number_of_entries)
        for sample_description in self.sample_description_table:
            sample_description.write(f)

    def get_size(self) -> int:
        table_all_size = 0
        for sample_description in self.sample_description_table:
            table_all_size += sample_description.get_size()
        return self.get_overall_size(1 + 3 + 4 + table_all_size)


class SampleDescription(Mp4Component):
    def __init__(self):
        super().__init__()
        self.sample_description_size: int = 0
        self.data_format: str = ""
        self.reserved1: bytes = b''
        self.data_reference_index: int = 0
        self.rest: bytes = b''

    def parse(self, f: BinaryIO):
        begin = f.tell()
        self.sample_description_size = self.read_int(f, 4)
        if self.sample_description_size == 0:
            return self
        self.data_format = self.read_ascii(f, 4)
        self.reserved1 = f.read(6)
        self.data_reference_index = self.read_int(f, 2)
        self.rest = f.read(self.sample_description_size - (f.tell() - begin))
        return self

    def print(self, depth=0):
        if self.sample_description_size == 0:
            self.print_with_indent("0", depth)
            return
        self.print_with_indent(f" - sample_description_size: {self.sample_description_size}", depth)
        self.print_with_indent(f" - data_format: {self.data_format}", depth)
        self.print_with_indent(f" - reserved1: {self.reserved1.hex()}", depth)
        self.print_with_indent(f" - data_reference_index: {self.data_reference_index}", depth)
        self.print_with_indent(f" - rest: {self.rest.hex()} \n", depth)

    def write(self, f: BinaryIO):
        if self.sample_description_size == 0:
            self.write_int(f, 0)
            return
        self.write_int(f, self.get_size())
        self.write_ascii(f, self.data_format)
        f.write(self.reserved1)
        self.write_int(f, self.data_reference_index, length=2)
        f.write(self.rest)

    def get_size(self) -> int:
        if self.sample_description_size == 0:
            return 4
        return 4 + 4 + 6 + 2 + len(self.rest)


class SttsBox(LeafBox):
    def __init__(self, box_type: str):
        super().__init__(box_type)
        self.version: bytes = b''
        self.flags: bytes = b''
        self.number_of_entries: int = 0
        self.time_to_sample_table: list[TimeToSample] = []

    def parse(self, f: BinaryIO, body_size: int):
        self.version = f.read(1)
        self.flags = f.read(3)
        self.number_of_entries = self.read_int(f, 4)
        for i in range(self.number_of_entries):
            self.time_to_sample_table.append(TimeToSample().parse(f))
        return self

    def print(self, depth=0):
        self.print_with_indent("stts", depth)
        depth += 1  # Increase the depth for nested printing
        self.print_with_indent(f" - version: {self.version.hex()}", depth)
        self.print_with_indent(f" - flags: {self.flags.hex()}", depth)
        self.print_with_indent(f" - number of entries: {self.number_of_entries}", depth)
        self.print_with_indent(f" - time to sample data:", depth)
        for time_to_sample in self.time_to_sample_table:
            time_to_sample.print(depth + 1)

    def write(self, f: BinaryIO):
        self.write_type_and_size(f, "stts", self.get_size())
        f.write(self.version)
        f.write(self.flags)
        self.write_int(f, self.number_of_entries)
        for sample_description in self.time_to_sample_table:
            sample_description.write(f)

    def get_size(self) -> int:
        all_size = 0
        for time_to_sample in self.time_to_sample_table:
            all_size += time_to_sample.get_size()
        return self.get_overall_size(1 + 3 + 4 + all_size)


class TimeToSample(Mp4Component):
    def __init__(self):
        super().__init__()
        self.sample_count = 0
        self.sample_delta = 0

    def parse(self, f: BinaryIO):
        self.sample_count = self.read_int(f, 4)
        self.sample_delta = self.read_int(f, 4)
        return self

    def print(self, depth=0):
        self.print_with_indent(f" - sample_count: {self.sample_count}, sample_delta: {self.sample_delta}", depth)

    def write(self, f: BinaryIO):
        self.write_int(f, self.sample_count)
        self.write_int(f, self.sample_delta)

    def get_size(self) -> int:
        return 8

class StscBox(LeafBox):
    def __init__(self, box_type: str):
        super().__init__(box_type)
        self.version: bytes = b''
        self.flags: bytes = b''
        self.number_of_entries: int = 0
        self.sample_to_chunk_table: list[SampleToChunk] = []

    def parse(self, f: BinaryIO, body_size: int):
        self.version = f.read(1)
        self.flags = f.read(3)
        self.number_of_entries = self.read_int(f, 4)
        for i in range(self.number_of_entries):
            self.sample_to_chunk_table.append(SampleToChunk().parse(f))
        return self

    def print(self, depth=0):
        self.print_with_indent("stsc", depth)
        depth += 1  # Increase the depth for nested printing
        self.print_with_indent(f" - version: {self.version.hex()}", depth)
        self.print_with_indent(f" - flags: {self.flags.hex()}", depth)
        self.print_with_indent(f" - number of entries: {self.number_of_entries}", depth)
        self.print_with_indent(f" - sample to chunk data:", depth)
        for sample_to_chunk in self.sample_to_chunk_table:
            sample_to_chunk.print(depth + 1)

    def write(self, f: BinaryIO):
        self.write_type_and_size(f, "stsc", self.get_size())
        f.write(self.version)
        f.write(self.flags)
        self.write_int(f, self.number_of_entries)
        for sample_description in self.sample_to_chunk_table:
            sample_description.write(f)

    def get_size(self) -> int:
        all_size = 0
        for sample_to_chunk in self.sample_to_chunk_table:
            all_size += sample_to_chunk.get_size()
        return self.get_overall_size(1 + 3 + 4 + all_size)


class SampleToChunk(Mp4Component):
    def __init__(self):
        super().__init__()
        self.first_chunk = 0
        self.samples_per_chunk = 0
        self.sample_description_id = 0

    def parse(self, f: BinaryIO):
        self.first_chunk = self.read_int(f, 4)
        self.samples_per_chunk = self.read_int(f, 4)
        self.sample_description_id = self.read_int(f, 4)
        return self

    def print(self, depth=0):
        self.print_with_indent(f" - first_chunk: {self.first_chunk}, samples_per_chunk: {self.samples_per_chunk}, sample_description_id:{self.sample_description_id}", depth)

    def write(self, f: BinaryIO):
        self.write_int(f, self.first_chunk)
        self.write_int(f, self.samples_per_chunk)
        self.write_int(f, self.sample_description_id)

    def get_size(self) -> int:
        return 12


