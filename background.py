import os
import game_world
from pico2d import *


class Background:
    _cache = {}

    def __init__(self, filename="bg1.png"):
        base_dir = os.path.dirname(__file__)
        image_path = os.path.join(base_dir, 'resource', 'Image', 'GUI', 'Stage', 'BackGround', filename)
        if filename not in Background._cache:
            Background._cache[filename] = load_image(image_path)
        self.image = Background._cache[filename]

    def draw(self):
        self.image.draw(get_canvas_width()//2, get_canvas_height()//2, get_canvas_width(), get_canvas_height())

    def draw_with_camera(self, camera):
        if not self.image:
            return
        offset_y = camera.y if camera else 0

        center_y = (self.image.h // 2) - offset_y
        self.image.draw(get_canvas_width()//2, center_y, get_canvas_width(), get_canvas_height()*2)

    def update(self):
        pass
