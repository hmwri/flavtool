import os.path

import parser


class Player:
    def __init__(self, path):
        self.f = open(path, "rb")
        self.parsed = parser.Parser(path).parse(read_mdat_bytes=False)
        self.t = 0


