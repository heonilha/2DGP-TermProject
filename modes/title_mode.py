from pico2d import *
import os
import game_framework
from modes import select_mode
image = None

def init():
    global image
    base_dir = os.path.dirname(os.path.dirname(__file__))
    image_path = os.path.join(base_dir, 'resource', 'Image', 'GUI', 'UI_TITLE_TITLE.jpg')
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: `{image_path}`")
    image = load_image(image_path)
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
    image.draw(600,350, 1200,700)
    update_canvas()
def update():
    pass
def pause():
    pass
def resume():
    pass