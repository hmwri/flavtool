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
composer.add_track(media_type="tast", data=np.array([[int(x/2+100)%256,int(x/2+200)%256,int(x/2+300)%256,int(x/2+400)%256,int(x/2)%256] for x in range(30003)]),codec="raw5", fps=60)

composer.compose()

composer.write("output.mp4")
import time



player = player.Player("output.mp4")
player.t = 0
player.play()
time.sleep(4)
player.stop()
