from component_base import Component
from component_transform import TransformComponent
from component_sprite import SpriteComponent
import game_framework


class MovementComponent(Component):
    def __init__(self, speed=200):
        super().__init__()
        self.xdir = 0
        self.ydir = 0
        self.speed = speed
        self.face_dir = 1  # 1 = right, -1 = left

    def update(self):
        dt = game_framework.frame_time
        tr = self.owner.get(TransformComponent)
        sprite = self.owner.get(SpriteComponent)

        if not tr:
            return

        # 방향 유지
        if self.xdir != 0:
            self.face_dir = self.xdir
            if sprite:
                sprite.flip = '' if self.face_dir == 1 else 'h'

        # 실제 이동
        tr.x += self.xdir * self.speed * dt
        tr.y += self.ydir * self.speed * dt
