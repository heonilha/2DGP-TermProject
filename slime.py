import os
from pico2d import *
import game_framework
import game_world
# 상수
FRAME_W = 21
FRAME_H = 21
FRAMES_COUNT = 6
SCALE = 2

HOP_DISTANCE = 40.0
HOP_HEIGHT = 12.0
HOP_DURATION = 0.25
HOP_INTERVAL = 1.0

ANIM_SPEED = 0.12
PREPARE_TIME = 0.4   # 점프 \('hop'\) 직전부터 애니메이션 시작

# 점프 애니메이션 프레임 인덱스
JUMP_AIR_FRAME = 1   # 공중에 있을 때 보여줄 프레임
JUMP_LAND_FRAME = 0  # 착지 후 보여줄 프레임


class Slime:
    def __init__(self):
        base_dir = os.path.dirname(__file__)
        image_path = os.path.join(base_dir, 'resource', 'Image', 'Monster', 'Blue_Slime.png')
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: `{image_path}`")
        self.image = load_image(image_path)

        self.hp = 10
        self.x = 500.0
        self.y_base = 300.0
        self.y = self.y_base

        # 기본 프레임은 착지 프레임으로 고정
        self.frame = JUMP_LAND_FRAME
        self.anim_timer = 0.0

        self.dir = -1
        self.jump_timer = 0.0

        # 준비(anticipation) 상태 플래그
        self.preparing = False

        self.hopping = False
        self.hop_timer = 0.0
        self.hop_start_x = self.x
        self.hop_target_x = self.x

        self.dead = False

    def _start_hop(self):
        # hop 시작: 준비 상태 종료, 공중 프레임 고정
        self.preparing = False
        self.hopping = True
        self.hop_timer = 0.0
        self.hop_start_x = self.x
        self.hop_target_x = self.x + self.dir * HOP_DISTANCE
        self.frame = JUMP_AIR_FRAME
        # 애니 타이머는 공중에서는 사용 안하므로 리셋
        self.anim_timer = 0.0

    def update(self):
        if self.dead:
            return

        dt = game_framework.frame_time

        # hop 타이머 업데이트
        self.jump_timer += dt

        # 준비 상태 진입: HOP_INTERVAL - PREPARE_TIME 시점
        if (not self.hopping) and (not self.preparing) and (self.jump_timer >= max(0.0, HOP_INTERVAL - PREPARE_TIME)):
            self.preparing = True
            self.anim_timer = 0.0
            # 준비 시작 시 프레임를 공격/예고 애니메이션의 첫 프레임으로 두고 애니 재생 시작
            self.frame = 0

        # hop 발동
        if self.jump_timer >= HOP_INTERVAL:
            self.jump_timer -= HOP_INTERVAL
            # 방향 반전 및 hop 시작
            self.dir *= -1
            # 준비 상태는 hop 시작과 함께 종료
            self.preparing = False
            self._start_hop()

        # hop 진행: 위치 보간 + 포물선형 바운스
        if self.hopping:
            self.hop_timer += dt
            t = min(self.hop_timer / HOP_DURATION, 1.0)
            self.x = self.hop_start_x + (self.hop_target_x - self.hop_start_x) * t
            bounce = 4.0 * t * (1.0 - t)
            self.y = self.y_base + bounce * HOP_HEIGHT
            # 공중에서는 공중 프레임 유지
            self.frame = JUMP_AIR_FRAME
            if t >= 1.0:
                # 착지: 위치 확정, 착지 프레임 설정
                self.hopping = False
                self.hop_timer = 0.0
                self.x = self.hop_target_x
                self.y = self.y_base
                self.frame = JUMP_LAND_FRAME
                self.anim_timer = 0.0
        else:
            # 준비 상태일 때만 애니메이션 재생(예고)
            if self.preparing:
                self.anim_timer += dt
                if self.anim_timer >= ANIM_SPEED:
                    self.anim_timer -= ANIM_SPEED
                    # 준비 애니메이션은 전체 프레임을 순환
                    self.frame = (self.frame + 1) % FRAMES_COUNT
            else:
                # 평상시: 애니메이션 없음, 항상 착지 프레임 유지
                self.frame = JUMP_LAND_FRAME
                self.anim_timer = 0.0
        if self.hp <= 0 and not self.dead:
            self.dead = True
            game_world.remove_object(self)

    def draw(self):
        left = int(self.frame) * FRAME_W
        bottom = 0
        draw_w = int(FRAME_W * SCALE)
        draw_h = int(FRAME_H * SCALE)
        flip = '' if self.dir < 0 else 'h'
        self.image.clip_composite_draw(left, bottom, FRAME_W, FRAME_H, 0, flip,
                                       self.x, self.y, draw_w, draw_h)
        if self.hp > 0:
            hp_bar_width = 50
            hp_bar_height = 5
            hp_bar_x = self.x - hp_bar_width // 2
            hp_bar_y = self.y + 40

            # 배경 (회색) - 색상을 튜플이 아닌 정수 인자로 전달
            draw_rectangle(hp_bar_x, hp_bar_y, hp_bar_x + hp_bar_width, hp_bar_y + hp_bar_height, 100, 100, 100)

            # 현재 HP (초록색)
            current_hp_width = int(hp_bar_width * (self.hp / 10))
            draw_rectangle(hp_bar_x, hp_bar_y, hp_bar_x + current_hp_width, hp_bar_y + hp_bar_height, 0, 255, 0)

    def get_bb(self):
        half_w = (FRAME_W * SCALE) / 2
        half_h = (FRAME_H * SCALE) / 2
        return self.x - half_w, self.y - half_h, self.x + half_w, self.y + half_h

    def handle_collision(self, group, other):
        pass
