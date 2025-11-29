import game_world
from components.component_base import Component


class ProjectileComponent(Component):
    def __init__(self, damage):
        super().__init__()
        self.damage = damage

    def on_hit(self, target):
        if hasattr(target, 'take_damage'):
            target.take_damage(self.damage)
        game_world.remove_object(self.owner)
