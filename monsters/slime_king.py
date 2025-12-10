import os
import random

from pico2d import get_canvas_height, get_canvas_width, load_image

import game_framework
import game_world
from behavior_tree import Action, BehaviorTree, Condition, Selector, Sequence
from collision_manager import CollisionGroup
from components.component_combat import CombatComponent
from components.component_collision import CollisionComponent
from components.component_hud import HUDComponent
from components.component_attack import AttackComponent
from components.component_move import MovementComponent, MovementType
from components.component_perception import PerceptionComponent
from components.component_sprite import SpriteComponent
from components.component_transform import TransformComponent
from game_object import GameObject

FRAME_W = 32
FRAME_H = 41
SCALE = 6  # 기존 대비 2배 확장해 거대한 보스 느낌을 줌
COLLISION_SCALE = 0.8  # 스프라이트 대비 더 축소한 히트박스

IDLE_FRAMES = [1, 2, 3]  # Idle/Hop 에서 사용할 프레임 인덱스
IDLE_ANIM_SPEED = 0.14

ATTACK_FRAME_COUNT = 6
ATTACK_STOP_FRAME_INDEX = 4  # 0-base, 5번째 프레임에서 돌진 정지
ATTACK_ANIM_SPEED = 0.12
ATTACK_COOLTIME = 2.5
ATTACK_DAMAGE = 25
ATTACK_HOLD_DURATION = 1.0  # 돌진 전 텀
CLOSE_ATTACK_RANGE = 180.0

HOP_DISTANCE = 55.0
HOP_HEIGHT = 16.0
HOP_DURATION = 0.32
HOP_INTERVAL = 1.4
HOP_PREPARE_TIME = 0.5

# 점프 공격 관련 상수
JUMP_ATTACK_COOLTIME = 4.0
JUMP_ATTACK_PROB = 0.2
JUMP_ATTACK_PROB_ENRAGE = 0.35
JUMP_ATTACK_MIN_RANGE = 220.0
JUMP_ATTACK_MAX_RANGE = 520.0
JUMP_PREPARE_DURATION = 1.0
JUMP_INITIAL_VELOCITY = 480.0
GRAVITY = -950.0
FALL_ANIM_SPEED = 0.08
LANDING_DAMAGE = 60


class SlimeKing(GameObject):
    def __init__(self):
        super().__init__()

        base_dir = os.path.dirname(os.path.dirname(__file__))
        idle_path = os.path.join(base_dir, "resource", "Image", "Monster", "SlimeKing Idle.png")
        attack_path = os.path.join(base_dir, "resource", "Image", "Monster", "SlimeKing Att.png")
        back_path = os.path.join(base_dir, "resource", "Image", "Monster", "SlimeKing Back.png")

        if not (os.path.exists(idle_path) and os.path.exists(attack_path) and os.path.exists(back_path)):
            raise FileNotFoundError("SlimeKing sprite resources are missing")

        start_x = random.randint(150, max(160, get_canvas_width() - 150))
        # 플레이어가 위로 올라가야 하는 보스 위치를 강조하기 위해 시작 y 값을 높임
        start_y = random.randint(int(get_canvas_height() * 1.3), get_canvas_height() * 2 - 220)

        self.transform = self.add_component(TransformComponent(start_x, start_y, FRAME_W * SCALE, FRAME_H * SCALE))
        self.sprite = self.add_component(SpriteComponent(load_image(idle_path), FRAME_W, FRAME_H))
        self.idle_image = self.sprite.image
        self.attack_image = load_image(attack_path)
        self.back_image = load_image(back_path)

        self.collision_group = CollisionGroup.MONSTER
        collision_w = self.transform.w * COLLISION_SCALE
        collision_h = self.transform.h * COLLISION_SCALE
        self.collision = self.add_component(
            CollisionComponent(
                group=CollisionGroup.MONSTER,
                mask=CollisionGroup.PLAYER | CollisionGroup.PROJECTILE,
                width=collision_w,
                height=collision_h,
            )
        )
        self.default_collision_mask = self.collision.mask
        self.combat = self.add_component(CombatComponent(50))
        self.movement = self.add_component(MovementComponent(70))
        self.perception = self.add_component(PerceptionComponent())
        # HP 바를 보스에 맞게 키우고 조금 더 위로 배치
        self.hud = self.add_component(HUDComponent(hp_width=80, hp_height=8, hp_offset=80))

        self.dir = -1
        self._update_sprite_flip()

        self.y_base = self.transform.y

        self.state = "idle"
        self.anim_timer = 0.0
        self.frame_indices = IDLE_FRAMES
        self.frame_index = 0
        self.frame_count = len(self.frame_indices)

        self.jump_timer = random.uniform(0.0, HOP_INTERVAL)
        self.preparing = False
        self.hopping = False

        self.attack_state = "none"
        self.attack_anim_timer = 0.0
        self.attack_cooltime_timer = ATTACK_COOLTIME
        self.attack_hold_timer = 0.0

        # 점프 공격 상태 값
        self.jump_attack_state = "none"  # none/prepare/air/landing/recover
        self.jump_attack_cooltime = JUMP_ATTACK_COOLTIME
        self.jump_attack_timer = self.jump_attack_cooltime
        self.vertical_velocity = 0.0
        self.horizontal_velocity = 0.0
        self.jump_target_x = self.x
        self.jump_target_y = self.y
        self.falling = False
        self.fall_anim_index = 0
        self.landing_attack_timer = 0.0
        self.jump_prepare_timer = 0.0

        self.bt = BehaviorTree(
            Selector(
                "SlimeKingSelector",
                Sequence("HandleJumpAttack", Condition("IsJumpAttacking", self.is_jump_attacking), Action("RunJumpAttack", self.run_jump_attack)),
                Sequence("StartJumpAttack", Condition("CanStartJumpAttack", self.can_start_jump_attack), Action("BeginJumpAttack", self.begin_jump_attack)),
                Sequence("HandleAttack", Condition("IsAttacking", self.is_attacking), Action("RunAttack", self.run_attack)),
                Sequence("StartAttack", Condition("CanAttack", self.can_attack), Action("BeginAttack", self.begin_attack)),
                Action("HandleHop", self.handle_hop),
            )
        )

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

    @property
    def frame(self):
        return self.sprite.frame

    @frame.setter
    def frame(self, value):
        if self.frame_count <= 0:
            self.sprite.frame = 0
        else:
            self.sprite.frame = value % self.frame_count

    @property
    def hp(self):
        return self.combat.hp

    @hp.setter
    def hp(self, value):
        self.combat.hp = max(0, min(self.combat.max_hp, value))

    def _update_sprite_flip(self):
        if self.sprite:
            self.sprite.flip = "" if self.dir < 0 else "h"

    def _set_animation(self, image, frames):
        # frames: 사용할 프레임 인덱스 배열 (0-base)
        self.sprite.image = image
        self.frame_indices = frames
        self.frame_count = len(frames)
        self.frame_index = 0
        self.frame = self.frame_indices[self.frame_index]

    def update(self, zag=None):
        if self.hp <= 0:
            game_world.remove_object(self)
            return

        if self.landing_attack_timer > 0:
            self.landing_attack_timer -= game_framework.frame_time

        self.perception.target = zag
        self.bt.run()
        super().update()

    def _advance_idle_anim(self, dt):
        self.anim_timer += dt
        if self.anim_timer >= IDLE_ANIM_SPEED:
            self.anim_timer -= IDLE_ANIM_SPEED
            self.frame_index = (self.frame_index + 1) % len(self.frame_indices)
            self.frame = self.frame_indices[self.frame_index]

    def handle_hop(self):
        dt = game_framework.frame_time

        if self.attack_state == "none" and self.jump_attack_state == "none":
            self.attack_cooltime_timer = min(ATTACK_COOLTIME, self.attack_cooltime_timer + dt)
            self.jump_attack_timer = min(self.jump_attack_cooltime, self.jump_attack_timer + dt)

        if not self.hopping and not self.movement.is_path_active():
            self.jump_timer += dt

        if (not self.hopping) and (not self.preparing) and (self.jump_timer >= max(0.0, HOP_INTERVAL - HOP_PREPARE_TIME)):
            self.preparing = True
            self.anim_timer = 0.0
            self._set_animation(self.idle_image, IDLE_FRAMES)

        if self.jump_timer >= HOP_INTERVAL:
            self.jump_timer -= HOP_INTERVAL
            self.dir *= -1
            self._update_sprite_flip()
            self.preparing = False
            self.hopping = True
            self._set_animation(self.idle_image, [IDLE_FRAMES[0]])
            self.movement.start_parabolic(
                (self.x, self.y_base),
                (self.x + self.dir * HOP_DISTANCE, self.y_base),
                HOP_HEIGHT,
                HOP_DURATION,
                on_complete=self._finish_hop,
            )
            return BehaviorTree.RUNNING

        if self.movement.type == MovementType.PARABOLIC:
            self.frame = IDLE_FRAMES[0]
        else:
            if self.preparing:
                self._advance_idle_anim(dt)
            else:
                if self.sprite.image is not self.idle_image or self.frame_indices != IDLE_FRAMES:
                    self._set_animation(self.idle_image, IDLE_FRAMES)
                self._advance_idle_anim(dt)
        return BehaviorTree.RUNNING

    def _finish_hop(self):
        self.hopping = False
        self.preparing = False
        self.frame_index = 0
        self.frame = IDLE_FRAMES[0]
        self.y_base = self.y

    def is_attacking(self):
        return BehaviorTree.SUCCESS if self.attack_state != "none" else BehaviorTree.FAIL

    def can_attack(self):
        if self.attack_state != "none" or self.hopping or self.preparing or self.jump_attack_state != "none":
            return BehaviorTree.FAIL

        distance = self.perception.distance_to_target()
        if distance is None:
            return BehaviorTree.FAIL

        if distance <= CLOSE_ATTACK_RANGE and self.attack_cooltime_timer >= ATTACK_COOLTIME:
            return BehaviorTree.SUCCESS
        return BehaviorTree.FAIL

    def begin_attack(self):
        target = self.perception.target
        if not target:
            return BehaviorTree.FAIL

        self.attack_state = "prepare"
        self.attack_anim_timer = 0.0
        self.attack_cooltime_timer = 0.0
        self.attack_hold_timer = 0.0
        self._set_animation(self.attack_image, list(range(ATTACK_FRAME_COUNT)))

        if target.x < self.x:
            self.dir = -1
        elif target.x > self.x:
            self.dir = 1
        self._update_sprite_flip()
        self.attack_start_pos = (self.x, self.y)
        self.attack_target_pos = (target.x, target.y)
        self.attack_dash_started = False
        return BehaviorTree.RUNNING

    def run_attack(self):
        dt = game_framework.frame_time

        if self.attack_state == "prepare":
            self.attack_anim_timer += dt
            if self.attack_anim_timer >= ATTACK_ANIM_SPEED:
                self.attack_anim_timer -= ATTACK_ANIM_SPEED
                if self.frame_index < ATTACK_STOP_FRAME_INDEX:
                    self.frame_index += 1
                    self.frame = self.frame_indices[self.frame_index]
                if self.frame_index >= ATTACK_STOP_FRAME_INDEX:
                    self.attack_state = "hold"
                    self.attack_hold_timer = 0.0
            return BehaviorTree.RUNNING

        if self.attack_state == "hold":
            self.attack_hold_timer += dt
            if self.attack_hold_timer >= ATTACK_HOLD_DURATION:
                self.attack_state = "dash"
                # 돌진 시작 시 6번째 프레임을 사용해 충격을 강조
                self.frame_index = ATTACK_FRAME_COUNT - 1
                self.frame = self.frame_indices[self.frame_index]
            return BehaviorTree.RUNNING

        if self.attack_state == "dash":
            if not self.attack_dash_started:
                self.movement.start_linear(
                    self.attack_start_pos,
                    self.attack_target_pos,
                    0.35,
                    on_complete=self._finish_attack_dash,
                )
                self.attack_dash_started = True
                return BehaviorTree.RUNNING
            if self.movement.is_path_active():
                return BehaviorTree.RUNNING
        return BehaviorTree.SUCCESS

    def _finish_attack_dash(self):
        self.attack_state = "none"
        self.attack_dash_started = False
        self._set_animation(self.idle_image, IDLE_FRAMES)
        self.frame = self.frame_indices[self.frame_index]
        self.y_base = self.y

    def is_jump_attacking(self):
        return BehaviorTree.SUCCESS if self.jump_attack_state != "none" else BehaviorTree.FAIL

    def can_start_jump_attack(self):
        if self.jump_attack_state != "none" or self.attack_state != "none" or self.hopping or self.preparing:
            return BehaviorTree.FAIL

        if self.jump_attack_timer < self.jump_attack_cooltime:
            return BehaviorTree.FAIL

        target = self.perception.target
        if not target:
            return BehaviorTree.FAIL

        distance_sq = self.perception.distance_sq_to_target()
        if not (
            JUMP_ATTACK_MIN_RANGE * JUMP_ATTACK_MIN_RANGE
            <= distance_sq
            <= JUMP_ATTACK_MAX_RANGE * JUMP_ATTACK_MAX_RANGE
        ):
            return BehaviorTree.FAIL

        prob = JUMP_ATTACK_PROB
        if self.hp <= self.combat.max_hp * 0.5:
            prob = JUMP_ATTACK_PROB_ENRAGE

        if random.random() <= prob:
            return BehaviorTree.SUCCESS
        return BehaviorTree.FAIL

    def begin_jump_attack(self):
        target = self.perception.target
        self.jump_attack_state = "prepare"
        self.jump_attack_timer = 0.0
        self.vertical_velocity = 0.0
        self.falling = False
        self.fall_anim_index = 0
        self.jump_prepare_timer = 0.0
        self._set_animation(self.back_image, [3])
        self.frame = 3

        # 플레이어 위치를 향해 점프하도록 목표 좌표를 설정
        target_x = target.x if target else self.x + self.dir * 80
        target_y = target.y if target else self.y_base
        self.jump_target_x = target_x
        self.jump_target_y = target_y

        if target:
            self.dir = -1 if target.x < self.x else 1
            self._update_sprite_flip()

        # 공중 공격 준비/도중에는 충돌을 완전히 비활성화
        self.collision.mask = 0
        return BehaviorTree.RUNNING

    def run_jump_attack(self):
        dt = game_framework.frame_time

        if self.jump_attack_state == "prepare":
            target = self.perception.target
            if target:
                distance_sq = self.perception.distance_sq_to_target()
                if not (
                    JUMP_ATTACK_MIN_RANGE * JUMP_ATTACK_MIN_RANGE
                    <= distance_sq
                    <= JUMP_ATTACK_MAX_RANGE * JUMP_ATTACK_MAX_RANGE
                ):
                    self.jump_attack_state = "none"
                    self.jump_attack_timer = 0.0
                    self.collision.mask = self.default_collision_mask
                    self._set_animation(self.idle_image, IDLE_FRAMES)
                    self.frame = self.frame_indices[self.frame_index]
                    return BehaviorTree.SUCCESS

                self.jump_target_x = target.x
                self.jump_target_y = target.y
                self.dir = -1 if target.x < self.x else 1
                self._update_sprite_flip()

            self.jump_prepare_timer += dt
            if self.jump_prepare_timer >= JUMP_PREPARE_DURATION:
                self.jump_attack_state = "air"
                self.vertical_velocity = JUMP_INITIAL_VELOCITY
                self.falling = False
                self.fall_anim_index = 0
                self.anim_timer = 0.0
                self._set_animation(self.back_image, [3, 2, 1, 0])
                self.frame = 3

                # 목표 y를 고려해 비행 시간을 계산한 뒤 x 속도를 설정
                start_y = self.y
                target_y = self.jump_target_y
                a = 0.5 * GRAVITY
                b = self.vertical_velocity
                c = start_y - target_y
                discriminant = b * b - 4 * a * c
                if discriminant >= 0:
                    sqrt_disc = discriminant ** 0.5
                    t1 = (-b + sqrt_disc) / (2 * a)
                    t2 = (-b - sqrt_disc) / (2 * a)
                    positive_times = [t for t in (t1, t2) if t > 0]
                    flight_time = max(positive_times) if positive_times else max(0.2, (2 * self.vertical_velocity) / abs(GRAVITY))
                else:
                    flight_time = max(0.2, (2 * self.vertical_velocity) / abs(GRAVITY))
                self.horizontal_velocity = (self.jump_target_x - self.x) / flight_time
            return BehaviorTree.RUNNING

        if self.jump_attack_state == "air":
            self.vertical_velocity += GRAVITY * dt
            self.x += self.horizontal_velocity * dt
            self.y += self.vertical_velocity * dt

            if not self.falling and self.vertical_velocity <= 0:
                self.falling = True
                self.anim_timer = 0.0
                self.fall_anim_index = 0
                self.frame = self.frame_indices[self.fall_anim_index]

            if self.falling:
                self.anim_timer += dt
                if self.anim_timer >= FALL_ANIM_SPEED and self.fall_anim_index < len(self.frame_indices) - 1:
                    self.anim_timer -= FALL_ANIM_SPEED
                    self.fall_anim_index += 1
                    self.frame = self.frame_indices[self.fall_anim_index]

            if self.falling and self.y <= self.jump_target_y:
                # self.y = self.jump_target_y
                self.jump_attack_state = "landing"
                self.landing_attack_timer = 0.2
                self.frame = self.frame_indices[-1]
                self.horizontal_velocity = 0.0
                self.vertical_velocity = 0.0
                self.collision.mask = self.default_collision_mask
                self.y_base = self.jump_target_y
                return BehaviorTree.RUNNING

        if self.jump_attack_state == "landing":
            # 착지 모션 완료 후 Idle 로 복귀
            self.jump_attack_state = "none"
            self._set_animation(self.idle_image, IDLE_FRAMES)
            self.frame = self.frame_indices[self.frame_index]
            return BehaviorTree.SUCCESS

        return BehaviorTree.RUNNING

    def handle_collision(self, other):
        if getattr(other, "collision_group", None) == CollisionGroup.PROJECTILE:
            self._enter_hit(other)
        elif getattr(other, "collision_group", None) == CollisionGroup.PLAYER:
            # 플레이어 근접 공격으로 명중했을 때 SlimeKing도 피해를 입도록 처리
            attack_comp = other.get(AttackComponent) if hasattr(other, "get") else None
            if attack_comp and attack_comp.is_attacking() and self not in attack_comp.hit_monsters:
                attack_comp.hit_monsters.append(self)
                if self.combat:
                    self.combat.take_damage(attack_comp.damage)

            # 점프 공격 중 착지 전에는 충돌 피해를 주지 않음
            if self.jump_attack_state == "air" and self.landing_attack_timer <= 0:
                return

            combat = getattr(other, "combat", None)
            if combat:
                if self.landing_attack_timer > 0:
                    combat.take_damage(LANDING_DAMAGE)
                else:
                    combat.take_damage(ATTACK_DAMAGE)

    def _enter_hit(self, attacker=None):
        if self.hp <= 0:
            return

        if self.movement.is_path_active():
            self.movement.type = MovementType.DIRECTIONAL

        self.attack_state = "none"
        self.attack_dash_started = False
        self.preparing = False
        self.hopping = False

        if self.jump_attack_state != "none":
            self.jump_attack_state = "none"
            self.collision.mask = self.default_collision_mask
            self.jump_attack_timer = 0.0

        self._set_animation(self.idle_image, IDLE_FRAMES)
        self.frame = self.frame_indices[self.frame_index]
        self.y_base = self.y

        if attacker and hasattr(attacker, "transform"):
            knock_dir = 1 if attacker.transform.x < self.x else -1
            self.x += knock_dir * 10
