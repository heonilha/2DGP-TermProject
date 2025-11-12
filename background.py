import os
import game_world
from pico2d import *


class Background:
    image = None

    def __init__(self):
        if Background.image == None:
            Background.image = load_image(os.path.join(r'C:\Users\heonilha\Documents\GitHub\2DGP-TermProject\resource\Image\GUI\Stage\BackGround\bg1.png'))
        self.image= Background.image
    def draw(self):
        self.image.draw(600, 350, 1200, 700)

    def update(self):
        pass