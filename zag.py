from pico2d import *
from sdl2 import SDL_KEYDOWN, SDLK_SPACE, SDLK_RIGHT, SDL_KEYUP, SDLK_LEFT, SDLK_UP, SDLK_DOWN

import os
import game_framework
import game_world
from state_machine import StateMachine
import title_mode
def space_down(e):  # e is space down ?
    return e[0] == 'INPUT' and e[1].type == SDL_KEYDOWN and e[1].key == SDLK_SPACE


def event_stop(e):
    return e[0] == 'STOP'

def event_run(e):
    return e[0] == 'RUN'

def event_die(e):
    return e[0] == 'DIE'

PIXEL_PER_METER = (10.0 / 0.5)  # 10 pixel 50 cm
RUN_SPEED_KMPH = 20.0  # Km / Hour
RUN_SPEED_MPM = (RUN_SPEED_KMPH * 1000.0 / 60.0)
RUN_SPEED_MPS = (RUN_SPEED_MPM / 60.0)
RUN_SPEED_PPS = (RUN_SPEED_MPS * PIXEL_PER_METER)

TIME_PER_ACTION = 0.5
IDLE_PER_TIME = 1.0 / TIME_PER_ACTION
FRAMES_PER_ACTION = 2
RUN_PER_TIME = 2.5 / TIME_PER_ACTION

# Die클래스 추가
# 죽으면 화면이 어두워지면서 타이틀 화면으로 넘어감
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
        self.frame = 0
        self.xdir = 0
        self.ydir = 0
        self.face_dir = 1
        self.hp = 10
        self.invincibleTimer = 0.0

        self.IDLE = Idle(self)
        self.RUN = Run(self)
        self.DIE = Die(self)
        self.state_machine = StateMachine(
            self.IDLE,
            state_transitions={
                self.IDLE: {space_down: self.IDLE, event_run: self.RUN, event_die: self.DIE},
                self.RUN: {space_down: self.RUN, event_stop: self.IDLE, event_die: self.DIE},
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

    def draw(self):
        if getattr(self.state_machine, 'cur_state', None) == self.DIE:
            self.DIE.draw()
            return

        if self.invincibleTimer>0:
            if int(self.invincibleTimer * 10) % 2 == 0:
                self.state_machine.draw()
        else:
            self.state_machine.draw()

    def handle_event(self, event):
        if event.key in (SDLK_RIGHT, SDLK_LEFT, SDLK_UP, SDLK_DOWN):
            cur_xdir, cur_ydir = self.xdir, self.ydir
            if event.type == SDL_KEYDOWN:
                if event.key == SDLK_RIGHT:
                    self.xdir += 1
                elif event.key == SDLK_LEFT:
                    self.xdir -= 1
                elif event.key == SDLK_UP:
                    self.ydir += 1
                elif event.key == SDLK_DOWN:
                    self.ydir -= 1

            elif event.type == SDL_KEYUP:
                if event.key == SDLK_RIGHT:
                    self.xdir -= 1
                elif event.key == SDLK_LEFT:
                    self.xdir += 1
                elif event.key == SDLK_UP:
                    self.ydir -= 1
                elif event.key == SDLK_DOWN:
                    self.ydir += 1
            if cur_xdir != self.xdir or cur_ydir != self.ydir:
                # 가로 방향이 변경되어 0이 아닌 경우 즉시 face_dir 업데이트
                if self.xdir != 0:
                    self.face_dir = self.xdir

                if self.xdir == 0 and self.ydir == 0:
                    self.state_machine.handle_state_event(('STOP', self.face_dir))
                else:
                    self.state_machine.handle_state_event(('RUN', None))
        else:
            self.state_machine.handle_state_event(('INPUT', event))

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
