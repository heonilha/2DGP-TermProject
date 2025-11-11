from pico2d import *
from sdl2 import SDL_KEYDOWN, SDLK_SPACE, SDLK_RIGHT, SDL_KEYUP, SDLK_LEFT, SDLK_UP, SDLK_DOWN

import game_framework
import game_world
from state_machine import StateMachine

def space_down(e):  # e is space down ?
    return e[0] == 'INPUT' and e[1].type == SDL_KEYDOWN and e[1].key == SDLK_SPACE


def event_stop(e):
    return e[0] == 'STOP'

def event_run(e):
    return e[0] == 'RUN'

PIXEL_PER_METER = (10.0 / 0.5)  # 10 pixel 50 cm
RUN_SPEED_KMPH = 20.0  # Km / Hour
RUN_SPEED_MPM = (RUN_SPEED_KMPH * 1000.0 / 60.0)
RUN_SPEED_MPS = (RUN_SPEED_MPM / 60.0)
RUN_SPEED_PPS = (RUN_SPEED_MPS * PIXEL_PER_METER)

TIME_PER_ACTION = 0.5
IDLE_PER_TIME = 1.0 / TIME_PER_ACTION
FRAMES_PER_ACTION = 2
RUN_PER_TIME = 2.5 / TIME_PER_ACTION

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
                self.zag.image.clip_composite_draw(int(self.zag.frame) * 32, 64, 32, 64, 0, 'h', self.zag.x, self.zag.y,32,64)
        elif self.zag.xdir==1:
            self.zag.image.clip_composite_draw(int(self.zag.frame) * 32, 0, 32, 64,0,'', self.zag.x, self.zag.y,32,64)
        else:
            self.zag.image.clip_composite_draw(int(self.zag.frame) * 32, 0, 32, 64, 0, 'h', self.zag.x, self.zag.y,32,64)

class Zag:
    def __init__(self):
        self.x, self.y = 400, 300
        self.image = load_image('ZAG_ani.png')
        self.frame = 0
        self.xdir = 0
        self.ydir = 0
        self.face_dir = 1

        self.IDLE = Idle(self)
        self.RUN = Run(self)
        self.state_machine = StateMachine(
            self.IDLE,
            state_transitions={
                self.IDLE: {space_down: self.IDLE, event_run: self.RUN},
                self.RUN: {space_down: self.RUN, event_stop: self.IDLE}
            }
        )
    def update(self):
        self.state_machine.update()

    def draw(self):
        self.state_machine.draw()

    def handle_event(self, event):
        if event.key in (SDLK_RIGHT, SDLK_LEFT, SDLK_UP, SDLK_DOWN):
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
            if self.xdir == 0 and self.ydir == 0:
                self.state_machine.handle_state_event(('STOP', self.face_dir))
            else:
                self.state_machine.handle_state_event(('RUN', None))
        else:
            self.state_machine.handle_state_event(('INPUT', event))