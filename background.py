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
        self.draw_with_camera(None)

    def draw_with_camera(self, camera):
        if not self.image:
            return

        canvas_w = get_canvas_width()
        canvas_h = get_canvas_height()

        offset_x = camera.x if camera else 0
        offset_y = camera.y if camera else 0

        max_x = max(0, self.image.w - canvas_w)
        max_y = max(0, self.image.h - canvas_h)

        source_x = clamp(0, offset_x, max_x)
        source_y = clamp(0, offset_y, max_y)

        self.image.clip_draw(int(source_x), int(source_y), canvas_w, canvas_h,
                             canvas_w // 2, canvas_h // 2, canvas_w, canvas_h)

    def update(self):
        pass
