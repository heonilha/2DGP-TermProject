import os
import random

from pico2d import *

import game_framework
import game_world
from components.component_sprite import SpriteComponent
from components.component_transform import TransformComponent
from game_object import GameObject

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

# 공격 관련 상수
ATTACK_RANGE = 100.0             # 공격 감지 범위
ATTACK_COOLTIME = 3.0            # 공격 쿨타임
ATTACK_ANIM_SPEED = 0.2          # 공격 준비 애니메이션 속도 (프레임당 0.2초)
ATTACK_HOLD_DURATION = 0.5       # 공격 전 1초 대기 시간
ATTACK_DASH_DURATION = 0.2       # 실제 돌진(dash)에 걸리는 시간



class Slime(GameObject):
    def __init__(self):
        super().__init__()
        base_dir = os.path.dirname(__file__)
        image_path = os.path.join(base_dir, 'resource', 'Image', 'Monster', 'Blue_Slime.png')
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: `{image_path}`")
        image = load_image(image_path)

        x = random.randint(100, 1100)
        y = random.randint(100, 600)
        self.transform = self.add_component(TransformComponent(x=x, y=y, w=FRAME_W * SCALE, h=FRAME_H * SCALE))
        self.sprite = self.add_component(SpriteComponent(image, FRAME_W, FRAME_H))

        self.hp = 10
        self.y_base = self.transform.y
        self.type = 'monster'

        # 슬라임별로 무작위의 점프 타이머 초기값 설정
        self.jump_timer = random.uniform(0.0, HOP_INTERVAL)
        self.sprite.frame = JUMP_LAND_FRAME
        self.anim_timer = 0.0

        self.dir = -1
        self.sprite.flip = 'h'

        # 준비(anticipation) 상태 플래그
        self.preparing = False

        self.hopping = False
        self.hop_timer = 0.0
        self.hop_start_x = self.transform.x
        self.hop_target_x = self.transform.x

        # 공격 관련 변수 초기화
        self.attack_range_squared = ATTACK_RANGE * ATTACK_RANGE
        self.attack_state = 'none'

        self.attack_cooltime = ATTACK_COOLTIME
        self.attack_cooltime_timer = self.attack_cooltime

        self.attack_anim_timer = 0.0
        self.attack_anim_speed = ATTACK_ANIM_SPEED

        self.hold_duration = ATTACK_HOLD_DURATION
        self.hold_timer = 0.0

        self.attack_duration = ATTACK_DASH_DURATION
        self.attack_timer = 0.0

        self.dead = False

    @property
    def x(self):
        return self.transform.x

    @x.setter
    def x(self, value):
        self.transform.x = value

    @property
    def y(self):
        return self.transform.y

    @y.setter
    def y(self, value):
        self.transform.y = value

    def _start_hop(self):
        self.preparing = False
        self.hopping = True
        self.hop_timer = 0.0
        self.hop_start_x = self.transform.x
        self.hop_target_x = self.transform.x + self.dir * HOP_DISTANCE
        self.sprite.frame = JUMP_AIR_FRAME
        self.anim_timer = 0.0

    def update(self, zag):
        if self.dead:
            return

        if self.hp <= 0 and not self.dead:
            self.dead = True
            game_world.remove_object(self)

        dt = game_framework.frame_time

        if self.attack_state == 'prepare':
            # "움직이지 않음" (즉, 위치 이동 코드가 없음)

            self.attack_anim_timer += dt
            if self.attack_anim_timer >= self.attack_anim_speed:
                self.attack_anim_timer -= self.attack_anim_speed

                if self.sprite.frame < 4:
                    self.sprite.frame += 1  # 프레임 0 -> 1 -> 2 -> 3

                # "프레임이 4가 되고"
                if self.sprite.frame == 4:
                    self.attack_state = 'hold'  # 'hold' 상태로 변경
                    self.hold_timer = 0.0  # 'hold' 타이머 리셋

            # 다른 모든 로직(점프 등)을 건너뛰어야 함
            return

            # 1-2. 'hold' 상태: 프레임 4에서 1초 대기
        elif self.attack_state == 'hold':
            # "움직이지 않음"
            self.sprite.frame = 4  # 프레임 4로 고정

            self.hold_timer += dt
            # "1초 기다렸다가"
            if self.hold_timer >= self.hold_duration:
                self.attack_state = 'dash'  # 'dash' 상태로 변경
                self.attack_timer = 0.0  # 'dash' 타이머 리셋

            # 다른 모든 로직 건너뛰기
            return

            # 1-3. 'dash' 상태: 목표 지점으로 돌진 (기존 is_attacking 로직)
        elif self.attack_state == 'dash':
            self.attack_timer += dt
            t = self.attack_timer / self.attack_duration

            if t >= 1.0:
                # 돌진 완료
                self.attack_state = 'none'  # 평상시 상태로 복귀
                self.transform.x, self.transform.y = self.attack_target_pos
                self.y_base = self.transform.y  # y_base 갱신 (중요!)
                self.attack_cooltime_timer = 0.0  # 쿨타임 시작
            else:
                # 돌진 중 (선형 보간)
                self.transform.x = (1 - t) * self.attack_start_pos[0] + t * self.attack_target_pos[0]
                self.transform.y = (1 - t) * self.attack_start_pos[1] + t * self.attack_target_pos[1]

            # 다른 모든 로직 건너뛰기
            return

            # ------------------------------------
            # --- 2. 'none' 상태 (평상시: 점프 & 공격 감지) ---
            # ------------------------------------
            # (self.attack_state가 'none'일 때만 아래 코드가 실행됨)

            # 쿨타임 갱신 (공격 중이 아닐 때만 시간이 흐름)
        self.attack_cooltime_timer += dt
        # hop 타이머 업데이트
        self.jump_timer += dt

        # 준비 상태 진입: HOP_INTERVAL - PREPARE_TIME 시점
        if (not self.hopping) and (not self.preparing) and (self.jump_timer >= max(0.0, HOP_INTERVAL - PREPARE_TIME)):
            self.preparing = True
            self.anim_timer = 0.0
            # 준비 시작 시 프레임를 공격/예고 애니메이션의 첫 프레임으로 두고 애니 재생 시작
            self.sprite.frame = 0

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
            self.transform.x = self.hop_start_x + (self.hop_target_x - self.hop_start_x) * t
            bounce = 4.0 * t * (1.0 - t)
            self.transform.y = self.y_base + bounce * HOP_HEIGHT
            # 공중에서는 공중 프레임 유지
            self.sprite.frame = JUMP_AIR_FRAME
            if t >= 1.0:
                # 착지: 위치 확정, 착지 프레임 설정
                self.hopping = False
                self.hop_timer = 0.0
                self.transform.x = self.hop_target_x
                self.transform.y = self.y_base
                self.sprite.frame = JUMP_LAND_FRAME
                self.anim_timer = 0.0
        else:
            # 준비 상태일 때만 애니메이션 재생(예고)
            if self.preparing:
                self.anim_timer += dt
                if self.anim_timer >= ANIM_SPEED:
                    self.anim_timer -= ANIM_SPEED
                    # 준비 애니메이션은 전체 프레임을 순환
                    self.sprite.frame = (self.sprite.frame + 1) % FRAMES_COUNT
            else:
                # 평상시: 애니메이션 없음, 항상 착지 프레임 유지
                self.sprite.frame = JUMP_LAND_FRAME
                self.anim_timer = 0.0

                # 플레이어와의 거리 제곱 계산
                distance_sq = (zag.x - self.transform.x) ** 2 + (zag.y - self.transform.y) ** 2

                # 사거리 내 + 쿨타임 완료 = 공격 시작!
                if (distance_sq <= self.attack_range_squared) and (self.attack_cooltime_timer >= self.attack_cooltime):

                    # --- 💥 공격 시작! (상태 변경) ---
                    self.attack_state = 'prepare'  # 'prepare' 상태로 진입
                    self.sprite.frame = 0  # 공격 애니메이션 0번 프레임부터
                    self.attack_anim_timer = 0.0  # 공격 애니메이션 타이머 리셋

                    # "현재" 슬라임 위치와 "현재" 플레이어 위치를 저장
                    # 이 값들은 돌진이 끝날 때까지 바뀌지 않음
                    self.attack_start_pos = (self.transform.x, self.transform.y)
                    self.attack_target_pos = (zag.x, zag.y)

                    # 플레이어의 x좌표와 비교하여 방향(dir)을 설정합니다.
                    if zag.x < self.x:
                        self.dir = -1  # 플레이어가 왼쪽에 있음 (왼쪽 보기)
                    elif zag.x > self.x:
                        self.dir = 1  # 플레이어가 오른쪽에 있음 (오른쪽 보기)

                else:
                    # 사거리 밖이거나 쿨타임 중 (아무것도 안 함)
                    pass

    def draw(self):
        self.sprite.flip = '' if self.dir < 0 else 'h'
        super().draw()
        if self.hp > 0:
            hp_bar_width = 50
            hp_bar_height = 5
            hp_bar_x = self.transform.x - hp_bar_width // 2
            hp_bar_y = self.transform.y + 40

            # 배경 (회색) - 색상을 튜플이 아닌 정수 인자로 전달
            draw_rectangle(hp_bar_x, hp_bar_y, hp_bar_x + hp_bar_width, hp_bar_y + hp_bar_height, 100, 100, 100)

            # 현재 HP (초록색)
            current_hp_width = int(hp_bar_width * (self.hp / 10))
            draw_rectangle(hp_bar_x, hp_bar_y, hp_bar_x + current_hp_width, hp_bar_y + hp_bar_height, 255, 0, 0)

    def get_distance_to_zag_sq(self, zag):
        dx = self.transform.x - zag.x
        dy = self.transform.y - zag.y
        return dx * dx + dy * dy

    def get_bb(self):
        half_w = self.transform.w / 2
        half_h = self.transform.h / 2
        return self.transform.x - half_w, self.transform.y - half_h, self.transform.x + half_w, self.transform.y + half_h

    def handle_collision(self, group, other):
        if group == 'ball:monster':
            self.take_damage(other.damage)
        pass

    def take_damage(self, damage):
        self.hp -= damage
        if self.hp <= 0:
            self.hp = 0
            player = game_world.player[0]
            # 3. 그 객체의 gold 변수를 직접 수정
            player.gold += 10

