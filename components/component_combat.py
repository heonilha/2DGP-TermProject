from components.component_base import Component
from components.component_state_machine import StateMachineComponent
import game_framework

class CombatComponent(Component):
    def __init__(self, max_hp, invincible_duration=0.0, enable_invincibility=False):
        super().__init__()
        self.hp = max_hp
        self.max_hp = max_hp
        self.invincible_timer = 0.0
        self.enable_invincibility = enable_invincibility
        self.invincible_duration = invincible_duration if enable_invincibility else 0.0

    def take_damage(self, dmg):
        if self.enable_invincibility and self.invincible_timer > 0:
            return

        self.hp -= dmg
        if self.hp <= 0:
            sm = self.owner.get(StateMachineComponent)
            if sm:
                sm.change_state("DEAD")
        elif self.enable_invincibility and self.invincible_duration > 0:
            # 피격 후 무적 시간
            self.invincible_timer = self.invincible_duration

    def update(self):
        if not self.enable_invincibility:
            return

        dt = game_framework.frame_time
        if self.invincible_timer > 0:
            self.invincible_timer -= dt
