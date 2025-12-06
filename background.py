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
        canvas_w, canvas_h = get_canvas_width(), get_canvas_height()
        image_h = self.image.h

        # Wrap the background vertically by splitting the image into two parts
        # relative to the camera's y-offset and drawing them in sequence.
        offset = offset_y % image_h

        upper_src_h = image_h - offset
        upper_dst_h = canvas_h * (upper_src_h / image_h)

        # Draw the upper portion (from the offset to the image top)
        if upper_dst_h > 0:
            self.image.clip_draw(
                0,
                offset,
                self.image.w,
                upper_src_h,
                canvas_w // 2,
                upper_dst_h / 2,
                canvas_w,
                upper_dst_h,
            )

        # Draw the remaining lower portion from the bottom of the image
        lower_src_h = offset
        lower_dst_h = canvas_h - upper_dst_h
        if lower_dst_h > 0 and lower_src_h > 0:
            self.image.clip_draw(
                0,
                0,
                self.image.w,
                lower_src_h,
                canvas_w // 2,
                upper_dst_h + (lower_dst_h / 2),
                canvas_w,
                lower_dst_h,
            )

    def update(self):
        pass
