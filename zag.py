from pico2d import *
from sdl2 import SDL_KEYDOWN, SDLK_z, SDLK_SPACE, SDLK_RIGHT, SDL_KEYUP, SDLK_LEFT, SDLK_UP, SDLK_DOWN, SDLK_a, SDLK_1, SDLK_2

import os
import game_framework
import game_world
from state_machine import StateMachine
from fire_ball import FireBall
from game_object import GameObject
from components.component_transform import TransformComponent
from components.component_sprite import SpriteComponent
from components.component_move import MovementComponent
from components.component_combat import CombatComponent
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
    def __init__(self, zag,attack_image):
        self.zag = zag
        self.attack_image = attack_image
        self.attack_timer = 0.0  # 공격 지속시간 타이머
        self.attack_duration = 0.2  # 총 공격 시간 (0.2초)
        self.hit_monsters = []  # ◀◀◀ [중요] 이번 공격에 맞은 몬스터 목록

    def enter(self,e):
        print("Zag Attack")
        self.attack_timer = self.attack_duration
        self.hit_monsters.clear()

        self.zag.attack_cooldown_timer = self.zag.attack_cooldown

    def exit(self,e):
        pass

    def do(self):
        self.attack_timer -= game_framework.frame_time

        # ◀◀◀ 공격 판정 시간 (예: 0.3초 중 0.1초~0.2초 사이)
        # (타이머가 0.2초 ~ 0.1초 남았을 때)
        if 0.1 < self.attack_timer < 0.2:
            self.check_attack_collision()

        # ◀◀◀ 공격 시간이 끝나면 IDLE또는 RUN으로 복귀
        if self.attack_timer <= 0:
            # ◀ zag의 xdir, ydir을 확인 (handle_event가 갱신해 줌)
            if self.zag.xdir != 0 or self.zag.ydir != 0:
                # ◀ 움직임이 있다면 RUN 상태로 복귀
                self.zag.state_machine.handle_state_event(('RUN', None))
            else:
                # ◀ 멈춰있다면 IDLE 상태로 복귀 (기존 TIME_OUT)
                self.zag.state_machine.handle_state_event(('TIME_OUT', None))
    def draw(self):
        # 원본/목표 크기 (원본 이미지 크기에 맞춰 필요하면 조정)
        src_w, src_h = 114, 217
        dest_w, dest_h = 32, 64

        # 슬라이스 수와 계산
        slices = 6
        slice_h_src = src_h // slices
        slice_h_dest = dest_h / slices

        # 공격 진행률 (0.0 ~ 1.0)
        progress = max(0.0, min(1.0, (self.attack_duration - self.attack_timer) / self.attack_duration))
        slices_to_draw = int(progress * slices)

        # 방향 플립과 기본 위치
        flip = 'h' if self.zag.face_dir == 1 else ''
        base_x = self.zag.x + (16 if self.zag.face_dir == 1 else -16)

        # 위에서부터 아래로 차례로 그리기
        base_top_y = self.zag.y + dest_h / 2 - slice_h_dest / 2
        for i in range(slices_to_draw):
            # src bottom 좌표: 이미지의 아래쪽 기준
            src_bottom = src_h - (i + 1) * slice_h_src
            dest_y = base_top_y - i * slice_h_dest
            self.attack_image.clip_composite_draw(0, src_bottom, src_w, slice_h_src,
                                                  0, flip, base_x, dest_y, dest_w, slice_h_dest)

        # 캐릭터 본체는 Zag.draw()에서 공통으로 처리

    def check_attack_collision(self):
        # 공격 이미지 크기는 폭 64, 높이 64로 가정

        attack_width = 64
        attack_height = 64
        attack_box_x = self.zag.x + (32 if self.zag.face_dir == 1 else -32)
        attack_box_y = self.zag.y
        attack_bb = (attack_box_x - attack_width // 2, attack_box_y - attack_height // 2,
                     attack_box_x + attack_width // 2, attack_box_y + attack_height // 2)
        for monster in game_world.all_objects():
            if monster == self.zag:
                continue
            if hasattr(monster, 'get_bb') and monster not in self.hit_monsters:
                monster_bb = monster.get_bb()
                if (attack_bb[0] < monster_bb[2] and attack_bb[2] > monster_bb[0] and
                    attack_bb[1] < monster_bb[3] and attack_bb[3] > monster_bb[1]):
                    # 충돌 판정이 일어났을 때 처리
                    monster.take_damage(5)  # 예: 20의 데미지
                    self.hit_monsters.append(monster)
                    print(f'Monster HP: {monster.hp}')


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
        import title_mode
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

    #self.zag.image.clip_draw(int(self.zag.frame) * 32, 0, 32, 64, self.zag.x, self.zag.y)
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
        attack_path = os.path.join(BASE_DIR, 'resource', 'Image', 'Character', 'ZAG_attack.png')
        self.attack_image = load_image(attack_path)
        self.movement = self.add_component(MovementComponent(RUN_SPEED_PPS))
        self.combat = self.add_component(CombatComponent(100))
        self.mp = 100
        self.attack_cooldown = 1.0  # 공격 쿨타임 (예: 1.0초)
        self.attack_cooldown_timer = 0.0  # 쿨타임 계산용 타이머 (0이 되어야 공격 가능)
        self.hp_potions = 3
        self.mp_potions = 3
        self.gold = 0
        self.type = 'player'

        self.keys_down = set()
        self.key_map = {
            SDLK_RIGHT: (1, 0),
            SDLK_LEFT: (-1, 0),
            SDLK_UP: (0, 1),
            SDLK_DOWN: (0, -1)
        }
        self.IDLE = Idle(self)
        self.RUN = Run(self)
        self.DIE = Die(self)
        self.ATTACK = Attack(self, self.attack_image)
        self.state_machine = StateMachine(
            self.IDLE,
            state_transitions={
                self.IDLE: {space_down: self.IDLE, event_run: self.RUN, event_die: self.DIE, event_attack: self.ATTACK},
                self.RUN: {space_down: self.RUN, event_stop: self.IDLE, event_die: self.DIE, event_attack: self.ATTACK},
                self.ATTACK: {event_timeout: self.IDLE, event_run: self.RUN, event_die: self.DIE},
                self.DIE: {},
            }
        )

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

    def draw(self):
        if getattr(self.state_machine, 'cur_state', None) == self.DIE:
            self.DIE.draw()
            return

        should_draw_body = True
        if self.invincibleTimer > 0:
            should_draw_body = int(self.invincibleTimer * 10) % 2 == 0

        if should_draw_body:
            super().draw()

        self.state_machine.draw()

        if self.hp > 0:
            hp_bar_width = 50
            hp_bar_height = 5
            hp_bar_x = self.x - hp_bar_width // 2
            hp_bar_y = self.y + 40

            draw_rectangle(hp_bar_x, hp_bar_y, hp_bar_x + hp_bar_width, hp_bar_y + hp_bar_height, 100, 100, 100)

            current_hp_width = int(hp_bar_width * (self.hp / self.combat.max_hp))
            draw_rectangle(hp_bar_x, hp_bar_y, hp_bar_x + current_hp_width, hp_bar_y + hp_bar_height, 255, 0, 0)

        if self.mp > 0:
            mp_bar_width = 50
            mp_bar_height = 5
            mp_bar_x = self.x - mp_bar_width // 2
            mp_bar_y = self.y + 50

            draw_rectangle(mp_bar_x, mp_bar_y, mp_bar_x + mp_bar_width, mp_bar_y + mp_bar_height, 100, 100, 100)

            current_mp_width = int(mp_bar_width * (self.mp / 100))
            draw_rectangle(mp_bar_x, mp_bar_y, mp_bar_x + current_mp_width, mp_bar_y + mp_bar_height, 0, 0, 255)

    def handle_event(self, event):
        if self.state_machine.cur_state == self.DIE:
            return

        if event.key in self.key_map:
            if event.type == SDL_KEYDOWN:
                self.keys_down.add(event.key)
            elif event.type == SDL_KEYUP:
                self.keys_down.discard(event.key)

        else:
            if event_attack(('INPUT', event)):
                if self.attack_cooldown_timer <= 0:
                    self.state_machine.handle_state_event(('INPUT', event))
            else:
                self.state_machine.handle_state_event(('INPUT', event))

        cur_xdir, cur_ydir = self.xdir, self.ydir

        self.xdir = 0
        self.ydir = 0
        for key in self.keys_down:
            if key in self.key_map:
                dx, dy = self.key_map[key]
                self.xdir += dx
                self.ydir += dy

        if cur_xdir != self.xdir or cur_ydir != self.ydir:
            if self.xdir != 0:
                self.face_dir = self.xdir

            if self.xdir == 0 and self.ydir == 0:
                self.state_machine.handle_state_event(('STOP', self.face_dir))
            else:
                self.state_machine.handle_state_event(('RUN', None))

        if event.type == SDL_KEYDOWN and event.key == SDLK_a:
            self.fire_ball()

        if event.type == SDL_KEYDOWN and event.key == SDLK_1:
            if self.hp_potions > 0:
                self.hp = min(self.combat.max_hp, self.hp + 20)
                self.hp_potions -= 1
                print(f'Used HP Potion. Current HP: {self.hp}, Remaining HP Potions: {self.hp_potions}')
            else:
                print("No HP potions left!")

        if event.type == SDL_KEYDOWN and event.key == SDLK_2:
            if self.mp_potions > 0:
                self.mp = min(100, self.mp + 20)
                self.mp_potions -= 1
                print(f'Used MP Potion. Current MP: {self.mp}, Remaining MP Potions: {self.mp_potions}')
            else:
                print("No MP potions left!")

    def get_bb(self):
        return self.x - (self.w / 2) + 10, \
               self.y - (self.h / 2) + 10, \
               self.x + (self.w / 2) - 10, \
               self.y + (self.h / 2) - 10

    def handle_collision(self, other, group):
        if group == 'zag:slime':
            if self.invincibleTimer <= 0.0:
                self.hp -= 10
                print(f'Zag HP: {self.hp}')
                self.invincibleTimer = 1.0

    def fire_ball(self):
        if self.mp >= 10:
            self.mp -= 10
        else:
            print("Not enough MP to cast Fireball!")
            return
        if self.xdir == 0 and self.ydir == 0:
            self.xdir = self.face_dir
        fireball = FireBall(self.x, self.y, self.xdir, self.ydir)
        game_world.add_object(fireball, 1)
