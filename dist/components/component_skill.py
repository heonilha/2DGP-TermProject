import math

import game_world

from components.component_base import Component
from components.component_move import MovementComponent
from components.component_transform import TransformComponent
from fire_ball import FireBall


class SkillComponent(Component):
    def __init__(self, mp_cost=10):
        super().__init__()
        self.mp_cost = mp_cost

    def fire_ball(self):
        owner = self.owner
        if not hasattr(owner, 'mp'):
            return

        if owner.mp < self.mp_cost:
            print("Not enough MP to cast Fireball!")
            return

        owner.mp -= self.mp_cost

        movement = owner.get(MovementComponent)
        transform = owner.get(TransformComponent)
        if not movement or not transform:
            return

        dir_x, dir_y = movement.xdir, movement.ydir
        if dir_x == 0 and dir_y == 0:
            dir_x = getattr(movement, 'face_dir', 1)

        norm = math.hypot(dir_x, dir_y)
        if norm != 0:
            dir_x /= norm
            dir_y /= norm

        fireball = FireBall(transform.x, transform.y, (dir_x, dir_y))
        game_world.add_object(fireball, 1)
