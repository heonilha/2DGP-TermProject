from pico2d import *

import game_framework
import game_world
from state_machine import StateMachine

TIME_PER_IDLE = 1.0
IDLE_PER_TIME = 1.0 / TIME_PER_IDLE
FRAMES_PER_IDLE = 2

class Idle:
    def __init__(self, zag):
        self.zag = zag

    def enter(self,e):
        pass

    def exit(self,e):
        pass

    def do(self):
        self.zag.frame = (self.zag.frame + FRAMES_PER_IDLE * IDLE_PER_TIME * game_framework.frame_time) % 2

    def draw(self):
        self.zag.image.clip_draw(int(self.zag.frame) * 32, 0,
                                 32, 64, self.zag.x, self.zag.y)

class Zag:
    def __init__(self):
        self.x, self.y = 400, 300
        self.image = load_image('ZAG_ani.png')
        self.frame = 0
        self.dir = 1

        self.IDLE = Idle(self)
        self.state_machine = StateMachine(
            self.IDLE,
            state_transitions={}
        )
    def update(self):
        self.state_machine.update()

    def draw(self):
        self.state_machine.draw()

    def handle_event(self, event):
        pass