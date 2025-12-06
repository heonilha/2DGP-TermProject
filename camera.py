from pico2d import get_canvas_width, get_canvas_height, clamp

class Camera:
    def __init__(self, world_width, world_height):
        self.x = 0
        self.y = 0
        self.world_w = world_width
        self.world_h = world_height

    def update(self, target):
        cw = get_canvas_width()
        ch = get_canvas_height()

        # 배경의 실제 월드 높이 = ch * 2
        world_h = ch * 2

        self.y = target.y - ch // 2

        # 카메라가 배경 밖으로 나가지 않게 제한
        self.y = clamp(0, self.y, world_h - ch)

