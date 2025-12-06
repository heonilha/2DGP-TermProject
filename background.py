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
        self.draw_with_camera(game_world.camera)

    def draw_with_camera(self, camera):
        if not self.image:
            return

        canvas_w = get_canvas_width()
        canvas_h = get_canvas_height()

        img_h = self.image.h
        img_w = self.image.w

        offset = int(camera.y % img_h) if camera else 0

        upper_h = min(img_h - offset, canvas_h)
        lower_h = max(0, canvas_h - upper_h)

        center_x = canvas_w // 2

        if upper_h > 0:
            upper_center_y = canvas_h - upper_h / 2
            self.image.clip_draw(0, offset, img_w, upper_h,
                                 center_x, upper_center_y,
                                 canvas_w, upper_h)

        if lower_h > 0:
            lower_center_y = lower_h / 2
            self.image.clip_draw(0, 0, img_w, lower_h,
                                 center_x, lower_center_y,
                                 canvas_w, lower_h)

    def update(self):
        pass
