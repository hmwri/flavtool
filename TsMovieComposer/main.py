import numpy as np

from TsMovieComposer.composer import Composer
from TsMovieComposer.parser import  Parser
from TsMovieComposer.analyzer import analyze

p = Parser("./tabemono.mp4")
root_box = p.parse()
flav_mp4 = analyze(root_box)
composer = Composer(flav_mp4)
composer.add_track(media_type="tast", data=np.array([[int(x/2+100)%256,int(x/2+200)%256,int(x/2+300)%256,int(x/2+400)%256,int(x/2)%256] for x in range(30003)], dtype=np.uint8),codec="raw5", fps=60)

composer.write("output.mp4")
p = Parser("output.mp4")
box = p.parse()


