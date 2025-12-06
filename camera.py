from pico2d import get_canvas_width, get_canvas_height, clamp


class Camera:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.world_width = get_canvas_width()
        self.world_height = get_canvas_height()

    def update(self, target):
        h = get_canvas_height()

        self.y = clamp(0, target.y - h // 4, self.world_height)
