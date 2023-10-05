import numpy as np

import composer
import player
from boxs.container import ContainerBox
import os
from parser import  Parser
from boxs.leaf import EditList
p = Parser("tabemono.mp4")
box = p.parse()

composer = composer.Composer(box)
composer.add_track(media_type="tast", data=np.array([[x%256,x%256,x%256,x%256,x%256] for x in range(30003)]),codec="raw5", fps=120)

composer.compose()

composer.write("output.mp4")


player = player.Player("output.mp4")

#
