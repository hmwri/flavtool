import numpy as np

import composer
from parser import  Parser

p = Parser("./tabemono.mp4")
box = p.parse()

composer = composer.Composer(box)
composer.add_track(media_type="tast", data=np.array([[int(x/2+100)%256,int(x/2+200)%256,int(x/2+300)%256,int(x/2+400)%256,int(x/2)%256] for x in range(30003)], dtype=np.uint8),codec="raw5", fps=60)

composer.compose(["soun", "vide"])

composer.write("output.mp4")
p = Parser("output.mp4")
box = p.parse()


