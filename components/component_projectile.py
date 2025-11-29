import game_world
from components.component_base import Component
from components.component_combat import CombatComponent


class ProjectileComponent(Component):
    def __init__(self, damage):
        super().__init__()
        self.damage = damage

    def on_hit(self, target):
        combat = target.get(CombatComponent) if hasattr(target, 'get') else None
        if combat:
            combat.take_damage(self.damage)
        elif hasattr(target, 'take_damage'):
            target.take_damage(self.damage)
        game_world.remove_object(self.owner)
