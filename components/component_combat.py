from component_base import Component
from component_state_machine import StateMachineComponent
import game_framework

class CombatComponent(Component):
    def __init__(self, max_hp):
        super().__init__()
        self.hp = max_hp
        self.max_hp = max_hp
        self.invincible_timer = 0.0

    def take_damage(self, dmg):
        if self.invincible_timer > 0:
            return

        self.hp -= dmg
        if self.hp <= 0:
            sm = self.owner.get(StateMachineComponent)
            if sm:
                sm.change_state("DEAD")
        else:
            # 피격 후 무적 시간
            self.invincible_timer = 0.5

    def update(self):
        dt = game_framework.frame_time
        if self.invincible_timer > 0:
            self.invincible_timer -= dt
