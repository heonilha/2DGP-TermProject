from pico2d import get_canvas_width, get_canvas_height


class Camera:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.world_width = get_canvas_width()
        self.world_height = get_canvas_height()

    def set_world_size(self, width: int, height: int):
        self.world_width = max(0, width)
        self.world_height = max(0, height)

    def update(self, target):
        h = get_canvas_height()
        max_y = max(0, self.world_height - h)
        target_y = target.y - h // 2
        self.y = max(0, min(target_y, max_y))
