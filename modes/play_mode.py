from pico2d import *

import game_framework
import game_world
import os
from modes import select_mode
from modes import title_mode
import camera

from zag import Zag
from monsters.goblin import Goblin
from monsters.goblin_archer import GoblinArcher
from monsters.slime import Slime
from monsters.slime_king import SlimeKing
from monsters.goblin_king import GoblinKing
from background import Background
from stage_definitions import STAGES
from ui import GameUI

zag = None
ui=None
monsters = []
game_running=True
current_stage_data = None
victory_timer = 2.0
defeat_timer = 2.0
world_cleared = False
persistent_player_state = {
    "gold": 0,
    "hp_potions": 3,
    "mp_potions": 3,
}

# 프로젝트의 루트 디렉토리를 기준으로 리소스 경로를 찾도록 설정
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
victory_image=None
victory_background=None
defeat_image=None
defeat_background=None
result_state = None

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
    global victory_image, victory_background, victory_timer, defeat_image, defeat_background, defeat_timer, result_state, world_cleared
    if current_stage_data is None:
        prepare_stage(1)
    image_path = os.path.join(BASE_DIR, 'resource', 'Image', 'GUI', 'clear.png')
    victory_image = load_image(image_path)
    victory_background_path = os.path.join(BASE_DIR, 'resource', 'Image', 'GUI','clearEmptyImage.png')
    victory_background = load_image(victory_background_path)
    victory_timer = 2.0

    defeat_path = os.path.join(BASE_DIR, 'resource', 'Image', 'GUI', 'defeat.png')
    defeat_image = load_image(defeat_path)
    defeat_background_path = os.path.join(BASE_DIR, 'resource', 'Image', 'GUI', 'clearEmptyImage.png')
    defeat_background = load_image(defeat_background_path)
    defeat_timer = 2.0
    result_state = None
    world_cleared = False

    game_world.camera = camera.Camera(1600,900)

    global zag
    # 플레이어가 패배 후 제목 화면으로 돌아갔다 다시 시작할 때
    # 남아 있던 상태(HP 0 등) 때문에 즉시 패배 화면이 뜨는 문제를 방지합니다.
    # 매ステ이지 시작 시 새 플레이어 객체를 생성해 완전히 초기화합니다.
    zag = Zag()
    _load_player_state()
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
    "SlimeKing": SlimeKing,
    "GoblinKing": GoblinKing,
}

MONSTER_CLASS_TUPLE = tuple(set(MONSTER_TYPES.values()))

def update():
    global game_running, victory_timer, defeat_timer, result_state, world_cleared
    if not game_running:
        if result_state == 'victory':
            victory_timer -= game_framework.frame_time
            if victory_timer <= 0:
                if not world_cleared:
                    _save_player_state()
                    game_world.clear()
                    world_cleared = True
                game_framework.change_mode(select_mode)
        elif result_state == 'defeat':
            defeat_timer -= game_framework.frame_time
            if defeat_timer <= 0:
                if not world_cleared:
                    _save_player_state()
                    game_world.clear()
                    world_cleared = True
                game_framework.change_mode(title_mode)

        return

    for layer in game_world.world:
        for o in layer[:]:  # 2. (안전성을 위해) 리스트의 복사본 순회

            if isinstance(o, MONSTER_CLASS_TUPLE):
                o.update(zag)
            else:
                o.update()

    if game_world.camera:
        game_world.camera.update(zag)
    game_world.handle_collisions()

    if zag and zag.hp <= 0:
        game_running = False
        result_state = 'defeat'
        defeat_timer = 2.0
        if not world_cleared:
            _save_player_state()
            game_world.clear()
            world_cleared = True
        return

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
        result_state = 'victory'
        _save_player_state()
        print("Victory! All monsters defeated.")


def draw():
    clear_canvas()
    if game_running:
        # 1. 게임이 실행 중일 때만 (평상시)
        #    게임 월드(플레이어, 몬스터, HP 바 등)를 그립니다.
        game_world.render()
        ui.draw(zag)
    else:
        # 2. 게임이 멈췄을 때 (승리/패배)
        #    게임 월드를 그리지 않고, 오직 결과 이미지만 그립니다.
        if result_state == 'victory' and victory_image:
            victory_background.draw(get_canvas_width() // 2, get_canvas_height() // 2, get_canvas_width()*2, get_canvas_height()*2)
            victory_image.draw(get_canvas_width() // 2, get_canvas_height() // 2)
        elif result_state == 'defeat' and defeat_image:
            defeat_background.draw(get_canvas_width() // 2, get_canvas_height() // 2, get_canvas_width()*2, get_canvas_height()*2)
            defeat_image.draw(get_canvas_width() // 2, get_canvas_height() // 2)

    update_canvas()


def finish():
    game_world.clear()


def _save_player_state():
    if zag is None:
        return

    persistent_player_state["gold"] = getattr(zag, "gold", persistent_player_state["gold"])
    persistent_player_state["hp_potions"] = getattr(zag, "hp_potions", persistent_player_state["hp_potions"])
    persistent_player_state["mp_potions"] = getattr(zag, "mp_potions", persistent_player_state["mp_potions"])


def _load_player_state():
    if zag is None:
        return

    zag.gold = persistent_player_state.get("gold", zag.gold)
    zag.hp_potions = persistent_player_state.get("hp_potions", zag.hp_potions)
    zag.mp_potions = persistent_player_state.get("mp_potions", zag.mp_potions)

def pause(): pass
def resume(): pass
