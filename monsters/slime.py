import os
import random

from pico2d import *

import game_framework
import game_world

from behavior_tree import Action, BehaviorTree, Condition, Selector, Sequence
from collision_manager import CollisionGroup
from components.component_combat import CombatComponent
from components.component_collision import CollisionComponent
from components.component_hud import HUDComponent
from components.component_move import MovementComponent, MovementType
from components.component_perception import PerceptionComponent
from components.component_projectile import ProjectileComponent
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

        base_dir = os.path.dirname(os.path.dirname(__file__))
        image_path = os.path.join(base_dir, 'resource', 'Image', 'Monster', 'Blue_Slime.png')
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: `{image_path}`")

        start_x = random.randint(100, 1100)
        start_y = random.randint(100, 600)

        self.transform = self.add_component(TransformComponent(start_x, start_y, FRAME_W * SCALE, FRAME_H * SCALE))
        self.sprite = self.add_component(SpriteComponent(load_image(image_path), FRAME_W, FRAME_H))
        self.collision_group = CollisionGroup.MONSTER
        self.collision = self.add_component(
            CollisionComponent(
                group=CollisionGroup.MONSTER,
                mask=CollisionGroup.PLAYER | CollisionGroup.PROJECTILE,
                width=FRAME_W * SCALE,
                height=FRAME_H * SCALE,
            )
        )
        self.combat = self.add_component(CombatComponent(10))
        self.movement = self.add_component(MovementComponent())
        self.perception = self.add_component(PerceptionComponent())
        self.hud = self.add_component(HUDComponent())

        self.y_base = self.transform.y

        self.jump_timer = random.uniform(0.0, HOP_INTERVAL)
        self.frame = JUMP_LAND_FRAME
        self.anim_timer = 0.0

        self.dir = -1
        self._update_sprite_flip()

        self.preparing = False
        self.hopping = False

        self.attack_state = 'none'
        self.attack_cooltime = ATTACK_COOLTIME
        self.attack_cooltime_timer = self.attack_cooltime
        self.attack_anim_timer = 0.0
        self.attack_anim_speed = ATTACK_ANIM_SPEED
        self.hold_duration = ATTACK_HOLD_DURATION
        self.hold_timer = 0.0
        self.attack_duration = ATTACK_DASH_DURATION
        self.attack_timer = 0.0
        self.attack_dash_started = False

        self.dead = False

        self.bt = BehaviorTree(
            Selector(
                'SlimeSelector',
                Sequence('HandleAttack', Condition('IsAttacking', self.is_attacking), Action('RunAttack', self.run_attack)),
                Sequence('StartAttack', Condition('CanAttack', self.can_attack), Action('BeginAttack', self.begin_attack)),
                Action('HandleHop', self.handle_hop),
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
        self.sprite.frame = value

    @property
    def hp(self):
        return self.combat.hp

    @hp.setter
    def hp(self, value):
        self.combat.hp = max(0, min(self.combat.max_hp, value))

    def _update_sprite_flip(self):
        if self.sprite:
            self.sprite.flip = '' if self.dir < 0 else 'h'

    def _finish_hop(self):
        self.hopping = False
        self.x = self.transform.x
        self.y = self.y_base
        self.frame = JUMP_LAND_FRAME
        self.anim_timer = 0.0

    def _update_prepare_animation(self, dt):
        self.anim_timer += dt
        if self.anim_timer >= ANIM_SPEED:
            self.anim_timer -= ANIM_SPEED
            self.frame = (self.frame + 1) % FRAMES_COUNT

    def update(self, zag=None):
        if self.dead:
            return

        if self.hp <= 0 and not self.dead:
            self.dead = True
            game_world.remove_object(self)
            return

        self.perception.target = zag

        self.bt.run()
        super().update()

    def is_attacking(self):
        return BehaviorTree.SUCCESS if self.attack_state != 'none' else BehaviorTree.FAIL

    def can_attack(self):
        if self.attack_state != 'none' or self.hopping or self.preparing:
            return BehaviorTree.FAIL

        if self.perception.is_in_range(ATTACK_RANGE) and self.attack_cooltime_timer >= self.attack_cooltime:
            return BehaviorTree.SUCCESS
        return BehaviorTree.FAIL

    def begin_attack(self):
        target = self.perception.target
        if not target:
            return BehaviorTree.FAIL

        self.attack_state = 'prepare'
        self.frame = 0
        self.attack_anim_timer = 0.0
        self.attack_start_pos = (self.x, self.y)
        self.attack_target_pos = (target.x, target.y)
        self.attack_dash_started = False

        if target.x < self.x:
            self.dir = -1
        elif target.x > self.x:
            self.dir = 1
        self._update_sprite_flip()
        return BehaviorTree.RUNNING

    def run_attack(self):
        dt = game_framework.frame_time

        if self.attack_state == 'prepare':
            self.attack_anim_timer += dt
            if self.attack_anim_timer >= self.attack_anim_speed:
                self.attack_anim_timer -= self.attack_anim_speed
                if self.frame < 4:
                    self.frame += 1
                if self.frame == 4:
                    self.attack_state = 'hold'
                    self.hold_timer = 0.0
            return BehaviorTree.RUNNING

        if self.attack_state == 'hold':
            self.frame = 4
            self.hold_timer += dt
            if self.hold_timer >= self.hold_duration:
                self.attack_state = 'dash'
                self.attack_timer = 0.0
            return BehaviorTree.RUNNING

        if self.attack_state == 'dash':
            if not self.attack_dash_started:
                self.movement.start_linear(
                    self.attack_start_pos,
                    self.attack_target_pos,
                    self.attack_duration,
                    on_complete=self._finish_attack_dash,
                )
                self.attack_dash_started = True
                return BehaviorTree.RUNNING

            if self.movement.is_path_active():
                return BehaviorTree.RUNNING

        return BehaviorTree.SUCCESS

    def _finish_attack_dash(self):
        self.attack_state = 'none'
        self.attack_cooltime_timer = 0.0
        self.y_base = self.y
        self.attack_dash_started = False

    def handle_hop(self):
        dt = game_framework.frame_time

        if self.attack_state == 'none':
            self.attack_cooltime_timer += dt

        if not self.hopping and not self.movement.is_path_active():
            self.jump_timer += dt

        if (not self.hopping) and (not self.preparing) and (self.jump_timer >= max(0.0, HOP_INTERVAL - PREPARE_TIME)):
            self.preparing = True
            self.anim_timer = 0.0
            self.frame = 0

        if self.jump_timer >= HOP_INTERVAL:
            self.jump_timer -= HOP_INTERVAL
            self.dir *= -1
            self._update_sprite_flip()
            self.preparing = False
            self.hopping = True
            self.frame = JUMP_AIR_FRAME
            self.movement.start_parabolic(
                (self.x, self.y_base),
                (self.x + self.dir * HOP_DISTANCE, self.y_base),
                HOP_HEIGHT,
                HOP_DURATION,
                on_complete=self._finish_hop,
            )
            return BehaviorTree.RUNNING

        if self.movement.type == MovementType.PARABOLIC:
            self.frame = JUMP_AIR_FRAME
        else:
            if self.preparing:
                self._update_prepare_animation(dt)
            else:
                self.frame = JUMP_LAND_FRAME
                self.anim_timer = 0.0

        return BehaviorTree.RUNNING

    def draw(self):
        super().draw()

    def get_distance_to_zag_sq(self, zag):
        dx = self.x - zag.x
        dy = self.y - zag.y
        return dx * dx + dy * dy

    def handle_collision(self, other):
        if getattr(other, "collision_group", None) == CollisionGroup.PROJECTILE:
            projectile_comp = other.get(ProjectileComponent)
            if projectile_comp:
                projectile_comp.on_hit(self)
        elif getattr(other, "collision_group", None) == CollisionGroup.PLAYER:
            combat = getattr(other, "combat", None)
            if combat:
                combat.take_damage(10)
