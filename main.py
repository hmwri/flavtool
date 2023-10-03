import numpy as np

import composer
from boxs.container import ContainerBox
import os
from parser import  Parser
from boxs.leaf import EditList
p = Parser("test.mp4")
box = p.parse()
# sound_track: ContainerBox = p.sound_track
# sound_track["mdia"]["minf"]["smhd"].balance = 100
# box["moov"]["mvhd"].time_scale=100
# box["moov"]["trak"]["mdia"]["mdhd"].time_scale = 3000

# box["moov"]["trak"]["edts"]["elst"].number_of_entries = 2
#
# box["moov"]["trak"]["edts"]["elst"].edit_list_table[0].track_duration = 2688000 - 24000*2
# box["moov"]["trak"]["edts"]["elst"].edit_list_table[0].media_time = 48000*10
#
#
# box["moov"]["trak"]["edts"]["elst"].edit_list_table.insert(
#     0,EditList(track_duration=1000, media_time=24000, media_rate=1)
# )
# # box["moov"]["trak"]["edts"]["elst"].edit_list_table.pop(1)
#
# eval = composer.Composer(box)
# eval.compose()
#
# p.parsed_box = eval.parsed

composer = composer.Composer(box)
# composer.add_track(media_type="tast", data=np.array([[x%256,x%256,x%256,x%256,x%256] for x in range(1003)]),codec="raw5", fps=30)

composer.compose()



composer.write("output.mp4")


p = Parser("output.mp4")
box = p.parse()



#
