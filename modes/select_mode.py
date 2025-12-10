from pico2d import *
import game_framework

from common import resource_path
from modes import play_mode
from stage_icon import StageIcon
from ui_icon import ShopIcon
import bgm_manager

# 3. 이 모드에서 사용할 객체 리스트
stage_icons = []
background = None


def init():
    global background, stage_icons

    # 배경 이미지 로드
    background_path = resource_path('resource/Image/GUI/clearEmptyImage.png')
    background = load_image(background_path)
    bgm_manager.play_select_bgm()
    icon1_path=resource_path('resource/Image/GUI/Stage/Icon/b1-1.png')
    icon2_path=resource_path('resource/Image/GUI/Stage/Icon/b2-1.png')
    shop_icon_path=resource_path('resource/Image/GUI/shop.png')

    # 스테이지 아이콘 객체 생성
    center_x, center_y = get_canvas_width() // 2, get_canvas_height() // 2
    offset_x = 150

    stage_icons = [
        StageIcon(center_x - offset_x, center_y, icon1_path, play_mode, stage_id=1),
        StageIcon(center_x + offset_x, center_y, icon2_path, play_mode, stage_id=2),
        ShopIcon(center_x, center_y - 200, shop_icon_path)
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