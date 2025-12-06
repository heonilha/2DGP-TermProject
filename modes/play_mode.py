from pico2d import *

import game_framework
import game_world
import os
from modes import select_mode
import camera

from zag import Zag
from monsters.goblin import Goblin
from monsters.goblin_archer import GoblinArcher
from monsters.slime import Slime
from background import Background
from stage_definitions import STAGES
from ui import GameUI

zag = None
ui=None
monsters = []
game_running=True
current_stage_data = None
victory_timer = 2.0

# 프로젝트의 루트 디렉토리를 기준으로 리소스 경로를 찾도록 설정
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
victory_image=None
victory_background=None

def handle_events():
    event_list = get_events()
    for event in event_list:
        if event.type == SDL_QUIT:
            game_framework.quit()
        elif event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
            game_framework.quit()
        else:
            zag.handle_event(event)

def prepare_stage(stage_id):
    global current_stage_data
    current_stage_data = STAGES[stage_id]


def init():
    global victory_image, victory_background, victory_timer
    if current_stage_data is None:
        prepare_stage(1)
    image_path = os.path.join(BASE_DIR, 'resource', 'Image', 'GUI', 'clear.png')
    victory_image = load_image(image_path)
    victory_background_path = os.path.join(BASE_DIR, 'resource', 'Image', 'GUI','clearEmptyImage.png')
    victory_background = load_image(victory_background_path)
    victory_timer = 2.0

    game_world.camera = camera.Camera(1600,900)

    global zag
    zag = Zag()
    game_world.add_object(zag, 1)
    _spawn_stage_monsters()

    global background
    background = Background(current_stage_data["background"])
    game_world.add_object(background, 0)
    global game_running
    game_running=True

    global ui
    ui=GameUI()

def _spawn_stage_monsters():
    global monsters
    monsters = []
    for mob_info in current_stage_data["monsters"]:
        mob_class = get_monster_class(mob_info["type"])
        for _ in range(mob_info["count"]):
            monster = mob_class()
            monsters.append(monster)
            game_world.add_object(monster, 1)


def get_monster_class(monster_type: str):
    monster_class = MONSTER_TYPES.get(monster_type)
    if monster_class is None:
        raise ValueError(f"Unknown monster type: {monster_type}")
    return monster_class


MONSTER_TYPES = {
    "Slime": Slime,
    "Goblin": Goblin,
    "GoblinArcher": GoblinArcher,
}

MONSTER_CLASS_TUPLE = tuple(set(MONSTER_TYPES.values()))

def update():
    global game_running, victory_timer
    if not game_running:
        victory_timer -= game_framework.frame_time  # ◀ 1-1. 타이머 감소

        if victory_timer <= 0:
            game_world.clear()
            game_framework.change_mode(select_mode)  # ◀ 1-2. 0초 되면 모드 변경

        return  # ◀ 1-3. (중요) 게임 월드 업데이트는 실행 안 함

    for layer in game_world.world:
        for o in layer[:]:  # 2. (안전성을 위해) 리스트의 복사본 순회

            if isinstance(o, MONSTER_CLASS_TUPLE):
                o.update(zag)
            else:
                o.update()

    if game_world.camera:
        game_world.camera.update(zag)
    game_world.handle_collisions()

    monster_exists = False
    for layer in game_world.world:
        for obj in layer:
            if isinstance(obj, MONSTER_CLASS_TUPLE):
                monster_exists = True
                break
        if monster_exists:
            break

    if not monster_exists:
        game_running = False
        victory_timer=2.0
        print("Victory! All monsters defeated.")


def draw():
    clear_canvas()
    if game_running:
        # 1. 게임이 실행 중일 때만 (평상시)
        #    게임 월드(플레이어, 몬스터, HP 바 등)를 그립니다.
        game_world.render()
        ui.draw(zag)
    else:
        # 2. 게임이 멈췄을 때 (승리)
        #    게임 월드를 그리지 않고, 오직 승리 이미지만 그립니다.
        if victory_image:
            victory_background.draw(get_canvas_width() // 2, get_canvas_height() // 2, get_canvas_width()*2, get_canvas_height()*2)
            victory_image.draw(get_canvas_width() // 2, get_canvas_height() // 2)

    update_canvas()


def finish():
    game_world.clear()

def pause(): pass
def resume(): pass
