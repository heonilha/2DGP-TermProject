from pico2d import get_canvas_width, get_canvas_height


class Camera:
    def __init__(self):
        self.x = 0
        self.y = 0

    def update(self, target):
        w = get_canvas_width()
        h = get_canvas_height()

        self.x = target.x - w // 2
        self.y = target.y - h // 2
