from pico2d import *
import game_framework
from modes import title_mode as start_mode

open_canvas(1200, 700)
game_framework.run(start_mode)
close_canvas()