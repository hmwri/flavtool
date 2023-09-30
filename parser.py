from typing import  *
import os
from boxs.container import ContainerBox

class Parser :
    def __init__(self, path):
        self.parsed_box = None
        self.path = path

    def parse(self):
        with open(self.path, "rb") as f:
            size = os.path.getsize(self.path)
            print(size)
            self.parsed_box = ContainerBox("root").parse(f, size)
            self.parsed_box.print(0)



        return self.parsed_box

    def write(self, path:str):
        with open(path, "wb") as f:
            self.parsed_box.write(f)





