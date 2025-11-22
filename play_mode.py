import random
from pico2d import *

import game_framework
import game_world
import os
import select_mode

from zag import Zag
from slime import Slime
from background import Background
from ui import GameUI

zag = None
ui=None
slimes = []
game_running=True

BASE_DIR=os.path.dirname(__file__)
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

def init():
    global victory_image,victory_background
    image_path = os.path.join(BASE_DIR, 'resource', 'Image', 'GUI', 'clear.png')
    victory_image = load_image(image_path)
    victory_background_path = os.path.join(BASE_DIR, 'resource', 'Image', 'GUI','clearEmptyImage.png')
    victory_background = load_image(victory_background_path)

    global zag
    zag = Zag()
    game_world.add_object(zag, 1)
    game_world.add_collision_pair(game_world.monsters,game_world.player,'zag:slime')
    game_world.add_collision_pair(game_world.projectiles, game_world.monsters, 'ball:monster')
    global slimes
    for i in range(5):
        slime = Slime()
        slimes.append(slime)
        game_world.add_object(slime, 1)
        game_world.add_collision_pair(game_world.player,game_world.monsters,'zag:slime')
    global background
    background=Background()
    game_world.add_object(background, 0)
    global game_running
    game_running=True
    victory_timer=2.0

    global ui
    ui=GameUI()

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

            # 3. 객체가 Slime 클래스의 인스턴스인지 확인
            if isinstance(o, Slime):
                # 4. 슬라임이면 "감독"이 알고 있는 zag(플레이어)를 넘겨줌
                o.update(zag)
            else:
                # 5. 플레이어, 배경 등 나머지는 그냥 원래대로 update() 호출
                o.update()
    game_world.handle_collisions()

    monster_exists = False
    for layer in game_world.world:
        for obj in layer:
            # 2. 객체가 Slime 클래스의 인스턴스(객체)인지 확인
            if isinstance(obj, Slime):
                # 3. 슬라임이 한 마리라도 발견되면, 아직 승리 아님
                monster_exists = True
                break  # 몬스터를 찾았으니 더 이상 검색할 필요 없음
        if monster_exists:
            break  # 몬스터를 찾았으니 더 이상 검색할 필요 없음

    # 4. 몬스터를 한 마리도 못 찾았다면(monster_exists가 False) 승리!
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
