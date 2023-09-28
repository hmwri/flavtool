from typing import BinaryIO



class Mp4Component:
    def __init__(self):
        pass


    def print(self, depth=0):
        raise NotImplemented

    def write(self, f: BinaryIO):
        raise NotImplemented

    def read_ascii(self, f, n):
        return f.read(n).decode("ascii")

    def read_int(self, f, n):
        return int.from_bytes(f.read(n), byteorder='big')

    def print_with_indent(self, word, depth):
        for d in range(depth):
            print("\t", end="")
        print(word)




    def read_fixed_float32(self, f):
        fixed_point_bytes = f.read(4)
        fixed_point_bytes = int.from_bytes(fixed_point_bytes, byteorder='big')
        integer_part = (fixed_point_bytes >> 16) & 0xFFFF
        fraction_part = fixed_point_bytes & 0xFFFF

        # 小数部分を2の-16乗を掛けて10進数に変換
        decimal_value = integer_part + (fraction_part / (2 ** 16))

        return decimal_value

    def write_fixed_float32(self, f, float_value):
        # 整数部と小数部に分ける
        integer_part = int(float_value)
        fraction_part = float_value - integer_part

        # 小数部分を2^16倍して16ビットの固定小数点に変換
        fraction_part_fixed = round(fraction_part * (2 ** 16))

        # 4バイトのバイト列に変換
        fixed_point_bytes = ((integer_part & 0xFFFF) << 16) | (fraction_part_fixed & 0xFFFF)
        byte_array = fixed_point_bytes.to_bytes(4, byteorder='big')

        # BinaryIOに書き込む
        f.write(byte_array)

    def read_fixed_float16(self, f):
        fixed_point_bytes = f.read(2)
        fixed_point_bytes = int.from_bytes(fixed_point_bytes, byteorder='big')
        # 上位8ビットが整数部分、下位8ビットが小数部分
        integer_part = (fixed_point_bytes >> 8) & 0xFF
        fraction_part = fixed_point_bytes & 0xFF

        # 小数部分を2の-8乗を掛けて10進数に変換
        decimal_value = integer_part + (fraction_part / (2 ** 8))

        return decimal_value

    def write_fixed_float16(self, f, float_value):
        # 整数部と小数部に分ける
        integer_part = int(float_value)
        fraction_part = float_value - integer_part

        # 小数部分を2^8倍して8ビットの固定小数点に変換
        fraction_part_fixed = round(fraction_part * (2 ** 8))

        # 2バイトのバイト列に変換
        fixed_point_bytes = ((integer_part & 0xFF) << 8) | (fraction_part_fixed & 0xFF)
        byte_array = fixed_point_bytes.to_bytes(2, byteorder='big')

        # BinaryIOに書き込む
        f.write(byte_array)

    def write_int(self, f: BinaryIO, n: int, length=4):
        f.write(n.to_bytes(length, 'big'))

    def write_ascii(self, f: BinaryIO, s: str):
        f.write(s.encode("ascii"))



    def get_size(self) -> int:
        raise NotImplementedError


class Box(Mp4Component):

    def __init__(self, box_type):
        super().__init__()
        self.box_type = box_type
        self.parent:Mp4Component= None


    def parse(self, f: BinaryIO, body_size: int):
        raise NotImplemented

    def print(self, depth=0):
        raise NotImplemented

    def write(self, f:BinaryIO):
        raise NotImplemented

    def get_size(self) -> int:
        raise NotImplementedError

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

    def get_overall_size(self, body_size):
        if body_size >= 4294967296 - 8:
            size = body_size + 16
        else:
            size = body_size + 8
        return size

    def write_type_and_size(self, f: BinaryIO, box_type: str, size: int, force_extended=False):
        if size >= 4294967296 or force_extended:
            self.write_int(f, 1)
            self.write_ascii(f, box_type)
            self.write_int(f, size, length=8)
        else:
            self.write_int(f, size)
            self.write_ascii(f, box_type)


