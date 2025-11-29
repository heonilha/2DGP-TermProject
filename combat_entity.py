from game_object import GameObject
from components.component_transform import TransformComponent
from components.component_combat import CombatComponent


class CombatEntity(GameObject):
    def __init__(self, x, y, w, h, layer=0, hp=100):
        super().__init__()
        self.transform = self.add_component(TransformComponent(x, y, w, h))
        self.combat = self.add_component(CombatComponent(hp))
        self.layer = layer

    @property
    def hp(self):
        return self.combat.hp

    @hp.setter
    def hp(self, value):
        self.combat.hp = max(0, min(self.combat.max_hp, value))

    def get_bb(self):
        half_w = self.transform.w * 0.5
        half_h = self.transform.h * 0.5
        return self.transform.x - half_w, self.transform.y - half_h, self.transform.x + half_w, self.transform.y + half_h

    def take_damage(self, amount):
        self.combat.take_damage(amount)
        if self.combat.hp <= 0:
            self.hp = 0
            self.on_death()

    def attack(self):
        pass

    def on_death(self):
        pass
