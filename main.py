
from boxs.container import ContainerBox
import os
from parser import  Parser

p = Parser("test.mp4")
box = p.parse()
sound_track: ContainerBox = p.sound_track
sound_track["mdia"]["minf"]["smhd"].balance = 100
# box["moov"]["mvhd"].time_scale=100
# box["moov"]["trak"]["mdia"]["mdhd"].time_scale = 3000
# box["moov"]["trak"]["mdia"]["hdlr"].component_subtype = "vido"

p.write("output.mp4")

p = Parser("output.mp4")
p.parse()
