import random
from pico2d import *

import game_framework
import game_world
import os

from zag import Zag
from slime import Slime
from background import Background

zag = None
slime = None

def handle_events():
    event_list = get_events()
    for event in event_list:
        if event.type == SDL_QUIT:
            game_framework.quit()
        elif event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
            game_framework.quit()
        else:
            zag.handle_event(event)

def init():
    global zag
    zag = Zag()
    game_world.add_object(zag, 1)
    game_world.add_collision_pair('zag:slime', zag, None)
    global slime
    slime = Slime()
    game_world.add_object(slime, 1)
    game_world.add_collision_pair('zag:slime', None, slime)
    global background
    background=Background()
    game_world.add_object(background, 0)


def update():
    game_world.update()
    game_world.handle_collisions()


def draw():
    clear_canvas()
    game_world.render()
    update_canvas()


def finish():
    game_world.clear()

def pause(): pass
def resume(): pass
