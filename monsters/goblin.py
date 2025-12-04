import os
import random

from pico2d import load_image, get_canvas_width

import game_framework
import game_world
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

FRAME_W = 30  # 210 / 7
FRAME_H = 35
FRAME_COUNT = 7
SCALE = 2

MOVE_ANIM_SPEED = 0.12
PREPARE_TIME = 1.0
ATTACK_ANIM_DURATION = 0.45
ATTACK_DASH_DURATION = 0.25
ATTACK_DISTANCE = 80
ATTACK_COOLDOWN = 2.0
ATTACK_DAMAGE = 15

DETECTION_RANGE = 220
PATROL_RADIUS = 140
HITBOX_EXTRA = 20


class Goblin(GameObject):
    def __init__(self):
        super().__init__()

        base_dir = os.path.dirname(os.path.dirname(__file__))
        image_path = os.path.join(base_dir, "resource", "Image", "Monster", "Goblin.png")
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: `{image_path}`")

        start_x = random.randint(120, max(130, get_canvas_width() - 120))
        start_y = random.randint(120, 400)

        self.transform = self.add_component(
            TransformComponent(start_x, start_y, FRAME_W * SCALE, FRAME_H * SCALE)
        )
        self.sprite = self.add_component(SpriteComponent(load_image(image_path), FRAME_W, FRAME_H))
        self.collision_group = CollisionGroup.MONSTER
        self.base_collision_w = self.transform.w - 10
        self.collision = self.add_component(
            CollisionComponent(
                group=CollisionGroup.MONSTER,
                mask=CollisionGroup.PLAYER | CollisionGroup.PROJECTILE,
                width=self.base_collision_w,
                height=self.transform.h - 10,
            )
        )
        self.combat = self.add_component(CombatComponent(30))
        self.movement = self.add_component(MovementComponent(90))
        self.perception = self.add_component(PerceptionComponent())
        self.hud = self.add_component(HUDComponent())

        self.dir = random.choice([-1, 1])
        self.movement.xdir = self.dir
        self._update_sprite_flip()

        self.patrol_left = start_x - PATROL_RADIUS
        self.patrol_right = start_x + PATROL_RADIUS

        self.anim_timer = 0.0

        self.state = "patrol"
        self.prepare_timer = 0.0
        self.attack_anim_timer = 0.0
        self.attack_hit_registered = False
        self.cooldown_timer = ATTACK_COOLDOWN

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
        self.sprite.frame = value % FRAME_COUNT

    @property
    def hp(self):
        return self.combat.hp

    @hp.setter
    def hp(self, value):
        self.combat.hp = max(0, min(self.combat.max_hp, value))

    def _update_sprite_flip(self):
        if self.sprite:
            self.sprite.flip = "" if self.dir >= 0 else "h"

    def update(self, target=None):
        if self.hp <= 0:
            game_world.remove_object(self)
            return

        self.perception.target = target

        if self.state == "patrol":
            self._update_patrol()
            if self._can_start_attack():
                self._start_prepare()
        elif self.state == "prepare":
            self._update_prepare()
        elif self.state == "attack":
            self._update_attack()
        elif self.state == "cooldown":
            self._update_cooldown()

        super().update()

    def _update_patrol(self):
        dt = game_framework.frame_time
        self.cooldown_timer = min(ATTACK_COOLDOWN, self.cooldown_timer + dt)

        if self.x <= self.patrol_left:
            self.dir = 1
        elif self.x >= self.patrol_right:
            self.dir = -1

        self.movement.xdir = self.dir
        self._update_sprite_flip()

        self.anim_timer += dt
        if self.anim_timer >= MOVE_ANIM_SPEED:
            self.anim_timer -= MOVE_ANIM_SPEED
            self.frame = (self.frame + 1) % 3

    def _can_start_attack(self):
        return (
            self.perception.target
            and self.perception.is_in_range(DETECTION_RANGE)
            and self.cooldown_timer >= ATTACK_COOLDOWN
        )

    def _start_prepare(self):
        target = self.perception.target
        if target:
            self.dir = -1 if target.x < self.x else 1
            self._update_sprite_flip()
        self.state = "prepare"
        self.prepare_timer = 0.0
        self.movement.xdir = 0
        self.frame = 3

    def _update_prepare(self):
        dt = game_framework.frame_time
        self.prepare_timer += dt
        if self.prepare_timer >= PREPARE_TIME:
            self._start_attack()

    def _start_attack(self):
        self.state = "attack"
        self.attack_anim_timer = 0.0
        self.attack_hit_registered = False
        self.cooldown_timer = 0.0

        start_pos = (self.x, self.y)
        end_pos = (self.x + self.dir * ATTACK_DISTANCE, self.y)

        self.collision.offset_x = self.dir * (HITBOX_EXTRA * 0.5)
        self.collision.override_width = self.transform.w + HITBOX_EXTRA

        self.movement.start_linear(
            start_pos, end_pos, ATTACK_DASH_DURATION, on_complete=self._finish_attack
        )

    def _update_attack(self):
        dt = game_framework.frame_time
        self.attack_anim_timer += dt

        progress = min(1.0, self.attack_anim_timer / ATTACK_ANIM_DURATION)
        frame_index = 4 + int(progress * 3)
        self.frame = min(frame_index, 6)

        if self.movement.type != MovementType.LINEAR and progress >= 1.0:
            self._finish_attack()

    def _finish_attack(self):
        self.state = "cooldown"
        self.collision.offset_x = 0
        self.collision.override_width = self.base_collision_w

    def _update_cooldown(self):
        dt = game_framework.frame_time
        self.cooldown_timer += dt
        if self.cooldown_timer >= ATTACK_COOLDOWN:
            self.state = "patrol"
            self.frame = 0

    def handle_collision(self, other):
        if getattr(other, "collision_group", None) == CollisionGroup.PROJECTILE:
            projectile_comp = other.get(ProjectileComponent) if hasattr(other, "get") else None
            projectile_component = getattr(other, "projectile", None)
            if projectile_comp:
                projectile_comp.on_hit(self)
            elif projectile_component:
                projectile_component.on_hit(self)
        elif getattr(other, "collision_group", None) == CollisionGroup.PLAYER and self.state == "attack":
            if not self.attack_hit_registered:
                combat = getattr(other, "combat", None)
                if combat:
                    combat.take_damage(ATTACK_DAMAGE)
                self.attack_hit_registered = True
