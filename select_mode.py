from pico2d import *
import game_framework
import game_world  # game_world에 등록해서 관리해도 됩니다.

import play_mode
from stage_icon import StageIcon
import os

BASE_DIR=os.path.dirname(__file__)

# 3. 이 모드에서 사용할 객체 리스트
stage_icons = []
background = None


def init():
    global background, stage_icons

    # 배경 이미지 로드
    background_path = os.path.join(BASE_DIR, 'resource','Image','GUI','clearEmptyImage.png')
    background = load_image(background_path)
    icon1_path=os.path.join(BASE_DIR, 'resource','Image','GUI','Stage','Icon','b1-1.png')
    icon2_path=os.path.join(BASE_DIR, 'resource','Image','GUI','Stage','Icon','b2-1.png')
    icon3_path=os.path.join(BASE_DIR, 'resource','Image','GUI','Stage','Icon','b3-1.png')
    icon4_path=os.path.join(BASE_DIR, 'resource','Image','GUI','Stage','Icon','b4-1.png')
    icon5_path=os.path.join(BASE_DIR, 'resource','Image','GUI','Stage','Icon','b5-1.png')

    # 스테이지 아이콘 객체 생성
    stage_icons = [
        StageIcon(200, 300, icon1_path, play_mode),
        StageIcon(400, 300, icon2_path, play_mode),
        StageIcon(600, 300, icon3_path, play_mode),
        StageIcon(800, 300, icon4_path, play_mode),
        StageIcon(1000, 300, icon5_path, play_mode)
    ]


def handle_events():
    event_list = get_events()
    for event in event_list:
        if event.type == SDL_QUIT:
            game_framework.quit()
        # (ESC 키로 메뉴로 돌아가기 등)

        # ⭐️ 핵심: '감독'이 '배우'들에게 이벤트를 전달
        for icon in stage_icons:
            icon.handle_event(event)


def update():
    for icon in stage_icons:
        icon.update()


def draw():
    clear_canvas()
    background.draw(get_canvas_width()/2, get_canvas_height()/2, get_canvas_width()*2, get_canvas_height()*2)
    for icon in stage_icons:
        icon.draw()
    update_canvas()


def finish():
    global stage_icons, background
    stage_icons = []
    background = None


def pause(): pass


def resume(): pass