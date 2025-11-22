from pico2d import *
from sdl2 import SDL_MOUSEBUTTONDOWN
import game_framework


class StageIcon:
    def __init__(self, x, y, image_path, target_mode):
        self.x, self.y = x, y
        self.image = load_image(image_path)
        self.w, self.h = self.image.w, self.image.h
        self.target_mode = target_mode # ◀ 클릭 시 이동할 '모드'

    def get_bb(self):
        # 마우스 충돌을 위한 사각형 범위
        return self.x - self.w / 2, self.y - self.h / 2, self.x + self.w / 2, self.y + self.h / 2

    def handle_event(self, event):
        # 1. 마우스 왼쪽 버튼을 눌렀을 때
        if event.type == SDL_MOUSEBUTTONDOWN and event.button == SDL_BUTTON_LEFT:
            #    이벤트 Y좌표(왼쪽 위 기준)를 그리기 Y좌표(왼쪽 아래 기준)로 변환합니다.
            mouse_y = get_canvas_height() - 1 - event.y
            # 3. get_bb()로 충돌 확인
            left, bottom, right, top = self.get_bb()
            if left <= event.x <= right and bottom <= mouse_y <= top:
                # 4. 클릭 성공! 게임 모드 변경
                game_framework.change_mode(self.target_mode)

    def update(self):
        # (마우스 호버 시 커진다거나 하는 애니메이션 추가 가능)
        pass

    def draw(self):
        self.image.draw(self.x, self.y)