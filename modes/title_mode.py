from pico2d import *
import os

from common import resource_path
import game_framework
from modes import select_mode
import bgm_manager
image = None

def init():
    global image
    image_path = resource_path('resource/Image/GUI/UI_TITLE_TITLE.jpg')
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: `{image_path}`")
    image = load_image(image_path)
    bgm_manager.play_title_bgm()
def finish():
    global image
    del image
def handle_events():
    event_list = get_events()
    for event in event_list:
        if event.type == SDL_QUIT:
            game_framework.quit()
        elif event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
            game_framework.quit()
        elif event.type == SDL_KEYDOWN and event.key == SDLK_SPACE:
            game_framework.change_mode(select_mode)
def draw():
    clear_canvas()
    image.draw(get_canvas_width()//2, get_canvas_height()//2, get_canvas_width(), get_canvas_height())
    update_canvas()
def update():
    pass
def pause():
    pass
def resume():
    pass