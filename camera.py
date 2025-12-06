from pico2d import clamp, get_canvas_width, get_canvas_height


class Camera:
    def __init__(self, world_width=None, world_height=None):
        self.x = 0
        self.y = 0
        self.world_width = world_width
        self.world_height = world_height

    def set_world_size(self, width, height):
        self.world_width = width
        self.world_height = height

    def update(self, target):
        w = get_canvas_width()
        h = get_canvas_height()

        self.x = 0

        desired_y = target.y - h // 2 if target.y > h // 2 else 0
        max_y = max(0, (self.world_height or h) - h)
        self.y = clamp(0, desired_y, max_y)
