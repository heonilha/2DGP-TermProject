import math

from pico2d import get_canvas_height, get_canvas_width

from collision_manager import CollisionGroup
import game_world
from game_object import GameObject
from components.component_collision import CollisionComponent
from components.component_move import MovementComponent, MovementType
from components.component_render import RenderComponent
from components.component_transform import TransformComponent
from components.component_projectile import ProjectileComponent


class Projectile(GameObject):
    def __init__(self, x, y, direction, speed, damage, width, height, image=None):
        super().__init__()
        self.collision_group = CollisionGroup.PROJECTILE

        self.transform = self.add_component(TransformComponent(x, y, width, height))
        self.movement = self.add_component(MovementComponent(speed))
        self.collision = self.add_component(
            CollisionComponent(
                group=CollisionGroup.PROJECTILE,
                mask=CollisionGroup.MONSTER,
                width=width,
                height=height,
            )
        )
        self.projectile = self.add_component(ProjectileComponent(damage))
        self.render = None

        if image:
            self.render = self.add_component(RenderComponent(image, width, height))

        self.set_direction(direction)

    def update(self):
        tr = self.transform
        move = self.movement
        super().update()

        if move and move.type == MovementType.DIRECTIONAL:
            cw = get_canvas_width()
            ch = get_canvas_height()
            hit_left = tr.x <= 200 and move.xdir < 0
            hit_right = tr.x >= cw - 200 and move.xdir > 0
            hit_bottom = tr.y <= 100 and move.ydir < 0
            hit_top = tr.y >= ch * 2 - 100 and move.ydir > 0

            if hit_left or hit_right or hit_bottom or hit_top:
                game_world.remove_object(self)

    def set_direction(self, direction):
        dx, dy = direction
        if dx == 0 and dy == 0:
            angle = 0.0
        else:
            angle = math.atan2(dy, dx)

        self.movement.xdir = math.cos(angle)
        self.movement.ydir = math.sin(angle)

        if self.render:
            self.render.rotation = angle

    def handle_collision(self, other):
        if getattr(other, "collision_group", None) == CollisionGroup.MONSTER:
            self.projectile.on_hit(other)
