from pico2d import *
from sdl2 import SDL_KEYDOWN, SDLK_z, SDLK_SPACE, SDLK_RIGHT, SDL_KEYUP, SDLK_LEFT, SDLK_UP, SDLK_DOWN

import os
import game_framework
import game_world
from state_machine import StateMachine

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
        self.attack_duration = 0.3  # 총 공격 시간 (0.5초)
        self.hit_monsters = []  # ◀◀◀ [중요] 이번 공격에 맞은 몬스터 목록

    def enter(self,e):
        print("Zag Attack")
        self.attack_timer = self.attack_duration
        self.hit_monsters.clear()

        self.zag.xdir = 0
        self.zag.ydir = 0
    def exit(self,e):
        pass

    def do(self):
        self.attack_timer -= game_framework.frame_time

        # ◀◀◀ 공격 판정 시간 (예: 0.3초 중 0.1초~0.2초 사이)
        # (타이머가 0.2초 ~ 0.1초 남았을 때)
        if 0.1 < self.attack_timer < 0.2:
            self.check_attack_collision()

        # ◀◀◀ 공격 시간이 끝나면 IDLE로 복귀
        if self.attack_timer <= 0:
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

        # 플레이어 원래 스프라이트도 함께 그림
        if self.zag.face_dir == 1:
            self.zag.image.clip_composite_draw(0, 0, 32, 64, 0, '', self.zag.x, self.zag.y, 32, 64)
        else:
            self.zag.image.clip_composite_draw(0, 0, 32, 64, 0, 'h', self.zag.x, self.zag.y, 32, 64)

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
                    monster.hp -= 5
                    self.hit_monsters.append(monster)
                    print(f'Monster HP: {monster.hp}')


class Die:
    def __init__(self, zag):
        self.zag = zag
        self.death_timer = 2.0  # 2초 후 타이틀 화면으로 이동
        self.defeat_image = load_image(os.path.join(r'C:\Users\heonilha\Documents\GitHub\2DGP-TermProject\resource\Image\GUI\defeat.png'))
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
        if self.zag.face_dir == 1:
            self.zag.image.clip_composite_draw(int(self.zag.frame) * 32, 0, 32, 64,0,'', self.zag.x, self.zag.y,32,64)
        else:
            self.zag.image.clip_composite_draw(int(self.zag.frame) * 32, 0, 32, 64,0,'h', self.zag.x, self.zag.y,32,64)
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
        self.zag.x += self.zag.xdir * RUN_SPEED_PPS * game_framework.frame_time
        self.zag.y += self.zag.ydir * RUN_SPEED_PPS * game_framework.frame_time
#composite_draw(self, left, bottom, width, height, angle, flip, x, y,w,h)
    def draw(self):
        if self.zag.xdir==0:
            if self.zag.face_dir == 1:
                self.zag.image.clip_composite_draw(int(self.zag.frame) * 32, 0, 32, 64,0,'', self.zag.x, self.zag.y,32,64)
            else:
                self.zag.image.clip_composite_draw(int(self.zag.frame) * 32, 0, 32, 64, 0, 'h', self.zag.x, self.zag.y,32,64)
        elif self.zag.xdir==1:
            self.zag.image.clip_composite_draw(int(self.zag.frame) * 32, 0, 32, 64,0,'', self.zag.x, self.zag.y,32,64)
        else:
            self.zag.image.clip_composite_draw(int(self.zag.frame) * 32, 0, 32, 64, 0, 'h', self.zag.x, self.zag.y,32,64)

class Zag:
    def __init__(self):
        self.x, self.y = 400, 300
        self.image = load_image(os.path.join(r'C:\Users\heonilha\Documents\GitHub\2DGP-TermProject\resource\Image\Character\ZAG_ani.png'))
        self.attack_image = load_image(os.path.join(r'C:\Users\heonilha\Documents\GitHub\2DGP-TermProject\resource\Image\Character\ZAG_attack.png'))
        self.frame = 0
        self.xdir = 0
        self.ydir = 0
        self.face_dir = 1
        self.hp = 50
        self.invincibleTimer = 0.0
        self.keys_down = set()
        self.key_map = {
            SDLK_RIGHT:(1,0),
            SDLK_LEFT:(-1,0),
            SDLK_UP:(0,1),
            SDLK_DOWN:(0,-1)
        }
        self.IDLE = Idle(self)
        self.RUN = Run(self)
        self.DIE = Die(self)
        self.ATTACK = Attack(self,self.attack_image)
        self.state_machine = StateMachine(
            self.IDLE,
            state_transitions={
                self.IDLE: {space_down: self.IDLE, event_run: self.RUN, event_die: self.DIE,event_attack: self.ATTACK},
                self.RUN: {space_down: self.RUN, event_stop: self.IDLE, event_die: self.DIE, event_attack: self.ATTACK},
                self.ATTACK: {event_timeout: self.IDLE, event_die: self.DIE},
                self.DIE: {}
            }
        )
    def update(self):
        if self.hp <= 0 and self.state_machine.cur_state != self.DIE:
            # 'DIE' 이벤트를 발생시켜 상태 머신이 DIE 상태로 변경하도록 함
            self.state_machine.handle_state_event(('DIE', None))
            # 사망 상태로 진입했다면, 즉시 Die.do()가 실행되도록 하고
            # 이번 프레임의 나머지 update(무적 타이머 감소 등)는 생략
            self.state_machine.update()
            return

        if self.invincibleTimer>0:
            self.invincibleTimer-= game_framework.frame_time
            if self.invincibleTimer<0:
                self.invincibleTimer=0.0
                print("무적시간 종료")
        self.state_machine.update()

    # python
    def draw(self):
        if getattr(self.state_machine, 'cur_state', None) == self.DIE:
            self.DIE.draw()
            return

        if self.invincibleTimer > 0:
            if int(self.invincibleTimer * 10) % 2 == 0:
                self.state_machine.draw()
        else:
            self.state_machine.draw()

        if self.hp > 0:
            hp_bar_width = 50
            hp_bar_height = 5
            hp_bar_x = self.x - hp_bar_width // 2
            hp_bar_y = self.y + 40

            # 배경 (회색) - 색상을 튜플이 아닌 정수 인자로 전달
            draw_rectangle(hp_bar_x, hp_bar_y, hp_bar_x + hp_bar_width, hp_bar_y + hp_bar_height, 100, 100, 100)

            # 현재 HP (초록색)
            current_hp_width = int(hp_bar_width * (self.hp / 50))
            draw_rectangle(hp_bar_x, hp_bar_y, hp_bar_x + current_hp_width, hp_bar_y + hp_bar_height, 0, 255, 0)

    def handle_event(self, event):
        # 1. ◀◀◀ [핵심 수정]
        #    죽었거나 공격 중일 때
        if self.state_machine.cur_state in (self.DIE, self.ATTACK):

            # ◀ '이동 키'의 'KEYUP' 이벤트는 특별히 처리해서 set에서 제거
            if event.type == SDL_KEYUP and event.key in self.key_map:
                self.keys_down.discard(event.key)

            # ◀ (필요시) 공격 중에 죽는 이벤트는 받아들일 수 있음
            # if event_die(('INPUT', event)):
            #    self.state_machine.handle_state_event(('DIE', None))

            # ◀ 그리고 나머지 모든 이벤트(KEYDOWN, Z, Space 등)는 무시
            return

        # 2. (이하 기존 'set' 방식 로직)
        #    살아있고, 공격 중이 아닐 때의 처리

        # 3. 이동 키인지 확인
        if event.key in self.key_map:
            if event.type == SDL_KEYDOWN:
                self.keys_down.add(event.key)
            elif event.type == SDL_KEYUP:
                self.keys_down.discard(event.key)

        # 4. 이동 키가 아니라면 (공격, 스페이스바 등)
        else:
            self.state_machine.handle_state_event(('INPUT', event))

        # 5. set을 기반으로 xdir/ydir을 매번 새로 계산
        cur_xdir, cur_ydir = self.xdir, self.ydir

        self.xdir = 0
        self.ydir = 0
        for key in self.keys_down:
            if key in self.key_map:
                dx, dy = self.key_map[key]
                self.xdir += dx
                self.ydir += dy

        # 6. 방향이 변경되었는지 확인하고 상태 전이
        if cur_xdir != self.xdir or cur_ydir != self.ydir:
            if self.xdir != 0:
                self.face_dir = self.xdir

            if self.xdir == 0 and self.ydir == 0:
                self.state_machine.handle_state_event(('STOP', self.face_dir))
            else:
                self.state_machine.handle_state_event(('RUN', None))
    def get_bb(self):
        return self.x - 16, self.y - 32, self.x + 16, self.y + 32

    def handle_collision(self, group, other):
        if group == 'zag:slime':
            if self.invincibleTimer <= 0.0:
                self.hp -= 10
                print(f'Zag HP: {self.hp}')
                self.invincibleTimer = 1.0
            else:
                pass
