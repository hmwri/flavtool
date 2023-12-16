import numpy as np

from flavtool.composer import Composer
from flavtool.parser import  Parser
from flavtool.analyzer import analyze

p = Parser("./tabemono.mp4")

root_box = p.parse()

root_box.print(0)
flav_mp4 = analyze(root_box)
composer = Composer(flav_mp4)
p = Parser("output.mp4")
box = p.parse()


