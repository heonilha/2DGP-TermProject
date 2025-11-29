from collision_manager import CollisionGroup
from game_object import GameObject
from components.component_transform import TransformComponent
from components.component_move import MovementComponent
from components.component_collision import CollisionComponent
from components.component_render import RenderComponent
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

    def set_direction(self, direction):
        dx, dy = direction
        self.movement.xdir = dx
        self.movement.ydir = dy

    def handle_collision(self, other):
        if getattr(other, "collision_group", None) == CollisionGroup.MONSTER:
            self.projectile.on_hit(other)
