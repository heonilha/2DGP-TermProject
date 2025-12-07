from pico2d import *
from sdl2 import SDL_KEYDOWN, SDLK_z, SDLK_SPACE, SDLK_RIGHT, SDLK_LEFT, SDLK_UP, SDLK_DOWN

import os
import game_framework
import game_world
from state_machine import StateMachine
from game_object import GameObject
from collision_manager import CollisionGroup
from components.component_transform import TransformComponent
from components.component_sprite import SpriteComponent
from components.component_move import MovementComponent
from components.component_combat import CombatComponent
from components.component_attack import AttackComponent
from components.component_skill import SkillComponent
from components.component_input import InputComponent
from components.component_collision import CollisionComponent


def space_down(e):  # e is space down ?
    return e[0] == 'INPUT' and e[1].type == SDL_KEYDOWN and e[1].key == SDLK_SPACE


def event_stop(e):
    return e[0] == 'STOP'

def event_run(e):
    return e[0] == 'RUN'

def event_die(e):
    return e[0] == 'DIE'

def event_attack(e):
    return e[0] == 'INPUT' and e[1].type == SDL_KEYDOWN and e[1].key == SDLK_z

def event_timeout(e):
    # 'TIME_OUT' 이벤트 (타이머가 다 되었을 때)
    return e[0] == 'TIME_OUT'

BASE_DIR = os.path.dirname(__file__)

PIXEL_PER_METER = (10.0 / 0.5)  # 10 pixel 50 cm
RUN_SPEED_KMPH = 20.0  # Km / Hour
RUN_SPEED_MPM = (RUN_SPEED_KMPH * 1000.0 / 60.0)
RUN_SPEED_MPS = (RUN_SPEED_MPM / 60.0)
RUN_SPEED_PPS = (RUN_SPEED_MPS * PIXEL_PER_METER)

TIME_PER_ACTION = 0.5
IDLE_PER_TIME = 1.0 / TIME_PER_ACTION
FRAMES_PER_ACTION = 2
RUN_PER_TIME = 2.5 / TIME_PER_ACTION

#Attack 클래스 추가
class Attack:
    def __init__(self, zag):
        self.zag = zag

    def enter(self, e):
        print("Zag Attack")
        attack_component = self.zag.get(AttackComponent)
        if attack_component:
            attack_component.start_attack(self.zag.face_dir)

    def exit(self, e):
        pass

    def do(self):
        attack_component = self.zag.get(AttackComponent)
        movement = self.zag.get(MovementComponent)
        if attack_component and not attack_component.is_attacking():
            if movement and (movement.xdir != 0 or movement.ydir != 0):
                self.zag.state_machine.handle_state_event(('RUN', None))
            else:
                self.zag.state_machine.handle_state_event(('TIME_OUT', None))

    def draw(self):
        pass

class Die:
    def __init__(self, zag):
        self.zag = zag
        self.death_timer = 2.0  # 2초 후 타이틀 화면으로 이동
        defeat_path = os.path.join(BASE_DIR, 'resource', 'Image', 'GUI', 'defeat.png')
        self.defeat_image = load_image(defeat_path)
    def enter(self,e):
        print("Zag is Dead")
        self.zag.invincibleTimer = 0.0
        pass

    def exit(self,e):
        pass

    def do(self):
        from modes import title_mode
        if self.death_timer <= 0:
            game_world.clear()
            game_framework.change_mode(title_mode)
        self.death_timer -= game_framework.frame_time
    def draw(self):

        if self.death_timer > 0.5:  # 0.5초 정도 남을 때까지 DEFEAT 표시
            self.defeat_image.draw(get_canvas_width() // 2, get_canvas_height() // 2)

class Idle:
    def __init__(self, zag):
        self.zag = zag

    def enter(self,e):
        if event_stop(e):
            self.zag.face_dir = e[1] # 이전 방향 유지

    def exit(self,e):
        pass

    def do(self):
        self.zag.frame = (self.zag.frame + FRAMES_PER_ACTION * IDLE_PER_TIME * game_framework.frame_time) % 2

    def draw(self):
        pass

class Run:
    def __init__(self, zag):
        self.zag = zag

    def enter(self,e):
        if self.zag.xdir != 0:
            self.zag.face_dir = self.zag.xdir

    def exit(self,e):
        pass

    def do(self):
        self.zag.frame = (self.zag.frame + FRAMES_PER_ACTION * RUN_PER_TIME * game_framework.frame_time) % 2
#composite_draw(self, left, bottom, width, height, angle, flip, x, y,w,h)
    def draw(self):
        pass

class Zag(GameObject):
    def __init__(self):
        super().__init__()

        self.transform = self.add_component(TransformComponent(400, 300, 48, 64))
        image_path = os.path.join(BASE_DIR, 'resource', 'Image', 'Character', 'ZAG_ani.png')
        self.sprite = self.add_component(SpriteComponent(load_image(image_path), 32, 64))
        attack_dir = os.path.join(BASE_DIR, 'resource', 'Image', 'Character', 'Attack')
        self.attack_images = [
            load_image(os.path.join(attack_dir, f'Attack{i}.png')) for i in range(1, 8)
        ]
        self.movement = self.add_component(MovementComponent(RUN_SPEED_PPS))
        self.combat = self.add_component(CombatComponent(100, invincible_duration=1.0, enable_invincibility=True))
        self.attack_component = self.add_component(AttackComponent(self.attack_images, duration=0.45, scale=0.7))
        self.skill_component = self.add_component(SkillComponent(mp_cost=10))
        self.input_component = self.add_component(
            InputComponent(
                {
                    SDLK_RIGHT: (1, 0),
                    SDLK_LEFT: (-1, 0),
                    SDLK_UP: (0, 1),
                    SDLK_DOWN: (0, -1),
                }
            )
        )
        self.collision_group = CollisionGroup.PLAYER
        self.collision = self.add_component(
            CollisionComponent(
                group=CollisionGroup.PLAYER,
                mask=CollisionGroup.MONSTER,
                width=self.transform.w - 20,
                height=self.transform.h - 20,
            )
        )

        self.mp = 100
        self.attack_cooldown = 1.0
        self.attack_cooldown_timer = 0.0
        self.hp_potions = 3
        self.mp_potions = 3
        self.gold = 0

        self.IDLE = Idle(self)
        self.RUN = Run(self)
        self.DIE = Die(self)
        self.ATTACK = Attack(self)
        self.state_machine = StateMachine(
            self.IDLE,
            state_transitions={
                self.IDLE: {space_down: self.IDLE, event_run: self.RUN, event_die: self.DIE, event_attack: self.ATTACK},
                self.RUN: {space_down: self.RUN, event_stop: self.IDLE, event_die: self.DIE, event_attack: self.ATTACK},
                self.ATTACK: {event_timeout: self.IDLE, event_run: self.RUN, event_die: self.DIE},
                self.DIE: {},
            },
        )
        self.state_machine.attack_state = self.ATTACK

    @property
    def x(self):
        return self.transform.x

    @x.setter
    def x(self, value):
        self.transform.x = value

    @property
    def y(self):
        return self.transform.y

    @y.setter
    def y(self, value):
        self.transform.y = value

    @property
    def w(self):
        return self.transform.w

    @property
    def h(self):
        return self.transform.h

    @property
    def xdir(self):
        return self.movement.xdir

    @xdir.setter
    def xdir(self, value):
        self.movement.xdir = value

    @property
    def ydir(self):
        return self.movement.ydir

    @ydir.setter
    def ydir(self, value):
        self.movement.ydir = value

    @property
    def face_dir(self):
        return self.movement.face_dir

    @face_dir.setter
    def face_dir(self, value):
        self.movement.face_dir = value
        self.sprite.flip = '' if value == 1 else 'h'

    @property
    def frame(self):
        return self.sprite.frame

    @frame.setter
    def frame(self, value):
        self.sprite.frame = value

    @property
    def hp(self):
        return self.combat.hp

    @hp.setter
    def hp(self, value):
        self.combat.hp = max(0, min(self.combat.max_hp, value))

    @property
    def invincibleTimer(self):
        return self.combat.invincible_timer

    @invincibleTimer.setter
    def invincibleTimer(self, value):
        self.combat.invincible_timer = max(0.0, value)

    def update(self):
        if self.hp <= 0 and self.state_machine.cur_state != self.DIE:
            self.state_machine.handle_state_event(('DIE', None))
            self.state_machine.update()
            return

        if self.attack_cooldown_timer > 0:
            self.attack_cooldown_timer -= game_framework.frame_time

        self.state_machine.update()
        super().update()

    def draw_with_camera(self, camera):
        if getattr(self.state_machine, 'cur_state', None) == self.DIE:
            self.DIE.draw()
            return

        should_draw_body = True
        if self.invincibleTimer > 0:
            should_draw_body = int(self.invincibleTimer * 10) % 2 == 0

        sprite = self.sprite
        original_visible = None
        if sprite:
            original_visible = sprite.visible
            sprite.visible = should_draw_body

        super().draw_with_camera(camera)

        if original_visible is not None:
            sprite.visible = original_visible

        self.state_machine.draw()

    def handle_event(self, event):
        if self.state_machine.cur_state == self.DIE:
            return

        if self.input_component:
            self.input_component.handle_event(event)

    def handle_collision(self, other):
        if getattr(other, "collision_group", None) == CollisionGroup.MONSTER:
            prev_hp = self.hp
            self.combat.take_damage(10)
            if self.hp < prev_hp:
                print(f'Zag HP: {self.hp}')

