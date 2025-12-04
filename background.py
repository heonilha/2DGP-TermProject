import os
import game_world
from pico2d import *


class Background:
    image = None

    def __init__(self):
        if Background.image is None:
            Background.image = load_image(
                os.path.join(r'C:\\Users\\heonilha\\Documents\\GitHub\\2DGP-TermProject\\resource\\Image\\GUI\\Stage\\BackGround\\bg1.png')
            )
        self.image = Background.image

    def draw(self):
        self.image.draw(get_canvas_width()//2, get_canvas_height()//2, get_canvas_width(), get_canvas_height())

    def update(self):
        pass
