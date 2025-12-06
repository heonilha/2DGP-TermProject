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
        self.image.draw(get_canvas_width()//2, get_canvas_height()//2, get_canvas_width(), get_canvas_height()*2)

    def draw_with_camera(self, camera):
        cw = get_canvas_width()
        ch = get_canvas_height()

        # 배경의 실제 렌더링 높이 (2배)
        bg_h = ch * 2

        # 카메라 offset
        offset_y = int(camera.y)

        # 배경의 중심 y = (배경 전체의 중앙) - offset
        center_y = bg_h // 2 - offset_y

        self.image.draw(
            cw // 2,
            center_y,
            cw,
            bg_h
        )

    def update(self):
        pass
