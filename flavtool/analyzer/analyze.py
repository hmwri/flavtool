from flavtool.parser.boxs.container import ContainerBox
from .flavMp4 import FlavMP4

def analyze(parsed_box: ContainerBox) -> FlavMP4:
    return FlavMP4(parsed_box)