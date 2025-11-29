from sdl2 import SDL_KEYDOWN, SDL_KEYUP, SDLK_1, SDLK_2, SDLK_a, SDLK_z

from components.component_base import Component
from components.component_move import MovementComponent
from components.component_skill import SkillComponent


def _is_attack_event(event):
    return event.type == SDL_KEYDOWN and event.key == SDLK_z


class InputComponent(Component):
    def __init__(self, key_map):
        super().__init__()
        self.key_map = key_map
        self.keys_down = set()

    def handle_event(self, event):
        owner = self.owner
        movement = owner.get(MovementComponent)
        if movement is None:
            return

        if owner.state_machine.cur_state == owner.DIE:
            return

        if event.key in self.key_map:
            if event.type == SDL_KEYDOWN:
                self.keys_down.add(event.key)
            elif event.type == SDL_KEYUP:
                self.keys_down.discard(event.key)
        else:
            if _is_attack_event(event):
                if getattr(owner, 'attack_cooldown_timer', 0) <= 0:
                    owner.state_machine.handle_state_event(('INPUT', event))
            else:
                owner.state_machine.handle_state_event(('INPUT', event))

        self._update_movement(movement)

        if event.type == SDL_KEYDOWN:
            if event.key == SDLK_a:
                skill = owner.get(SkillComponent)
                if skill:
                    skill.fire_ball()
            elif event.key == SDLK_1:
                self._use_hp_potion()
            elif event.key == SDLK_2:
                self._use_mp_potion()

    def _update_movement(self, movement):
        owner = self.owner
        cur_xdir, cur_ydir = movement.xdir, movement.ydir
        movement.xdir = 0
        movement.ydir = 0

        for key in self.keys_down:
            if key in self.key_map:
                dx, dy = self.key_map[key]
                movement.xdir += dx
                movement.ydir += dy

        if owner.state_machine.is_attacking():
            return

        if cur_xdir != movement.xdir or cur_ydir != movement.ydir:
            if movement.xdir != 0:
                movement.face_dir = movement.xdir
                if owner.sprite:
                    owner.sprite.flip = '' if movement.face_dir == 1 else 'h'

            if movement.xdir == 0 and movement.ydir == 0:
                owner.state_machine.handle_state_event(('STOP', movement.face_dir))
            else:
                owner.state_machine.handle_state_event(('RUN', None))

    def _use_hp_potion(self):
        owner = self.owner
        if getattr(owner, 'hp_potions', 0) > 0:
            owner.hp = min(owner.combat.max_hp, owner.hp + 20)
            owner.hp_potions -= 1
            print(f'Used HP Potion. Current HP: {owner.hp}, Remaining HP Potions: {owner.hp_potions}')
        else:
            print("No HP potions left!")

    def _use_mp_potion(self):
        owner = self.owner
        if getattr(owner, 'mp_potions', 0) > 0:
            owner.mp = min(100, owner.mp + 20)
            owner.mp_potions -= 1
            print(f'Used MP Potion. Current MP: {owner.mp}, Remaining MP Potions: {owner.mp_potions}')
        else:
            print("No MP potions left!")
