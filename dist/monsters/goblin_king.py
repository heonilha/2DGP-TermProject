import math
import os
import random

from pico2d import get_canvas_width, get_canvas_height, load_image

from common import resource_path
import game_framework
import game_world
from collision_manager import CollisionGroup
from components.component_combat import CombatComponent
from components.component_collision import CollisionComponent
from components.component_hud import HUDComponent
from components.component_move import MovementComponent
from components.component_perception import PerceptionComponent
from components.component_sprite import SpriteComponent
from components.component_transform import TransformComponent
from game_object import GameObject
from projectile import BombProjectile, MissileProjectile

IDLE_FRAME_W = 41
IDLE_FRAME_H = 51
IDLE_ANIM_PATTERN = [0, 1, 2, 1]
IDLE_ANIM_SPEED = 0.14

HIT_DURATION = 0.3
INVINCIBLE_DURATION = 0.3

BOMB_FRAME_W = 41
BOMB_FRAME_H = 55
BOMB_FRAME_COUNT = 6
BOMB_ANIM_SPEED = 0.12
BOMB_DAMAGE = 10
BOMB_FLIGHT_GRAVITY = -200.0

GUN_FRAME_W = 54
GUN_FRAME_H = 52
GUN_FRAME_COUNT = 6
GUN_ANIM_SPEED = 0.1
MISSILE_DAMAGE = 5
MISSILE_SPEED = 420.0

BACKRUN_FRAME_W = 45
BACKRUN_FRAME_H = 50
BACKRUN_FRAME_COUNT = 5
BACKRUN_SPEED = 180.0
BACKRUN_DURATION = 1.1
BACKRUN_JUMP_VY = 150.0

HIGH_ALTITUDE_RATIO = 1.8

ATTACK_COOLDOWN = 2.5
DETECTION_RANGE = 360.0
BACKRUN_RANGE = 130.0
BOMB_ATTACK_RANGE = 260.0

SCALE = 2


class GoblinKing(GameObject):
    def __init__(self):
        super().__init__()
        img_dir = "resource/Image/Monster"

        idle_path = resource_path(f"{img_dir}/GoblinKingIdle.png")
        hit_path = resource_path(f"{img_dir}/Goblin KingHit.png")
        bomb_path = resource_path(f"{img_dir}/GoblinKing Bomb.png")
        gun_path = resource_path(f"{img_dir}/GoblinKing Att.png")
        back_path = resource_path(f"{img_dir}/GoblinKing BackRun.png")
        bomb_proj_path = resource_path(f"{img_dir}/bomb.png")
        missile_path = resource_path(f"{img_dir}/GoblinKingMissile.png")
        explosion_paths = [
            resource_path(f"{img_dir}/hit_4x4_1.png"),
            resource_path(f"{img_dir}/hit_4x4_2.png"),
            resource_path(f"{img_dir}/hit_4x4_3.png"),
        ]

        if not all(os.path.exists(p) for p in [
            idle_path,
            hit_path,
            bomb_path,
            gun_path,
            back_path,
            bomb_proj_path,
            missile_path,
            *explosion_paths,
        ]):
            raise FileNotFoundError("GoblinKing sprite resources are missing")

        self.idle_image = load_image(idle_path)
        self.hit_image = load_image(hit_path)
        self.bomb_image = load_image(bomb_path)
        self.gun_image = load_image(gun_path)
        self.back_image = load_image(back_path)
        self.bomb_proj_image = load_image(bomb_proj_path)
        self.missile_image = load_image(missile_path)
        self.explosion_images = [load_image(p) for p in explosion_paths]

        start_x = random.randint(200, max(220, get_canvas_width() - 200))
        start_y = random.randint(int(get_canvas_height() * 1.4), get_canvas_height() * 2 - 250)

        self.transform = self.add_component(
            TransformComponent(
                start_x,
                start_y,
                IDLE_FRAME_W * SCALE,
                max(IDLE_FRAME_H, BOMB_FRAME_H) * SCALE,
            )
        )
        self.sprite = self.add_component(SpriteComponent(self.idle_image, IDLE_FRAME_W, IDLE_FRAME_H))

        self.collision_group = CollisionGroup.MONSTER
        self.collision = self.add_component(
            CollisionComponent(
                group=CollisionGroup.MONSTER,
                mask=CollisionGroup.PLAYER | CollisionGroup.PROJECTILE,
                width=self.transform.w * 0.75,
                height=self.transform.h * 0.8,
            )
        )
        self.combat = self.add_component(
            CombatComponent(60, invincible_duration=INVINCIBLE_DURATION, enable_invincibility=True)
        )
        self.base_speed = 120
        self.movement = self.add_component(MovementComponent(self.base_speed))
        self.perception = self.add_component(PerceptionComponent())
        self.hud = self.add_component(HUDComponent(hp_width=90, hp_height=10, hp_offset=80))

        self.dir = -1
        self._update_sprite_flip()

        self.state = "idle"
        self.prev_state = "idle"
        self.anim_timer = 0.0
        self.anim_index = 0

        self.attack_timer = 0.0
        self.attack_fired = False

        self.hit_timer = 0.0

        self.backrun_timer = 0.0
        self.vertical_velocity = 0.0

    @property
    def x(self):
        return self.transform.x

    @property
    def y(self):
        return self.transform.y

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
            self.sprite.flip = "" if self.dir < 0 else "h"

    def _set_animation(self, image, frame_w, frame_h, index=0):
        self.sprite.image = image
        self.sprite.frame_w = frame_w
        self.sprite.frame_h = frame_h
        self.sprite.frame = index
        self.anim_index = 0
        self.anim_timer = 0.0

    def _is_airborne(self):
        return abs(self.vertical_velocity) > 1e-3

    def _prefer_bombs_only(self):
        canvas_height = get_canvas_height()
        return self.transform.y >= canvas_height * HIGH_ALTITUDE_RATIO

    def update(self, zag=None):
        if self.hp <= 0:
            game_world.remove_object(self)
            return

        self.perception.target = zag

        if self.hit_timer > 0:
            self.hit_timer -= game_framework.frame_time
            if self.hit_timer <= 0:
                self.state = self.prev_state
                self._restore_animation_for_state()

        if self.state == "idle":
            self._update_idle(zag)
        elif self.state == "bomb_attack":
            self._update_bomb_attack(zag)
        elif self.state == "gun_attack":
            self._update_gun_attack(zag)
        elif self.state == "backrun":
            self._update_backrun(zag)
        elif self.state == "hit":
            pass

        self.attack_timer = min(ATTACK_COOLDOWN, self.attack_timer + game_framework.frame_time)

        super().update()

    def _update_idle(self, zag):
        dt = game_framework.frame_time
        self.anim_timer += dt
        if self.anim_timer >= IDLE_ANIM_SPEED:
            self.anim_timer -= IDLE_ANIM_SPEED
            self.anim_index = (self.anim_index + 1) % len(IDLE_ANIM_PATTERN)
            self.frame = IDLE_ANIM_PATTERN[self.anim_index]

        if zag:
            self.dir = -1 if zag.x < self.x else 1
            self._update_sprite_flip()
            if self._is_airborne():
                return
            if self.perception.is_in_range(BACKRUN_RANGE) and self._can_backrun():
                self._start_backrun()
                return
            if self._prefer_bombs_only():
                if self.attack_timer >= ATTACK_COOLDOWN and self.perception.is_in_range(DETECTION_RANGE):
                    self._start_bomb_attack(zag)
                return
            if self.perception.is_in_range(DETECTION_RANGE) and self.attack_timer >= ATTACK_COOLDOWN:
                if self.perception.is_in_range(BOMB_ATTACK_RANGE):
                    self._start_bomb_attack(zag)
                else:
                    if random.random() < 0.5:
                        self._start_gun_attack(zag)
                    else:
                        self._start_bomb_attack(zag)

    def _start_bomb_attack(self, zag):
        self.state = "bomb_attack"
        self.attack_timer = 0.0
        self.attack_fired = False
        self._set_animation(self.bomb_image, BOMB_FRAME_W, BOMB_FRAME_H)
        self.frame = 0
        if zag:
            self.dir = -1 if zag.x < self.x else 1
            self._update_sprite_flip()
        self.movement.xdir = 0
        self.movement.ydir = 0

    def _update_bomb_attack(self, zag):
        dt = game_framework.frame_time
        self.anim_timer += dt
        if self.anim_timer >= BOMB_ANIM_SPEED:
            self.anim_timer -= BOMB_ANIM_SPEED
            self.frame += 1
            if self.frame >= BOMB_FRAME_COUNT:
                self.state = "idle"
                self._set_animation(self.idle_image, IDLE_FRAME_W, IDLE_FRAME_H)
                self.frame = IDLE_ANIM_PATTERN[self.anim_index % len(IDLE_ANIM_PATTERN)]
                return

        if self.frame == BOMB_FRAME_COUNT - 1 and not self.attack_fired:
            self.attack_fired = True
            target_ref = zag if zag else (self.x + self.dir * 120, self.y)
            bomb = BombProjectile(
                self.x,
                self.y,
                target_ref,
                self.bomb_proj_image,
                self.explosion_images,
                damage=BOMB_DAMAGE,
                gravity=BOMB_FLIGHT_GRAVITY,
            )
            game_world.add_object(bomb)

    def _start_gun_attack(self, zag):
        self.state = "gun_attack"
        self.attack_timer = 0.0
        self.attack_fired = False
        self._set_animation(self.gun_image, GUN_FRAME_W, GUN_FRAME_H)
        self.frame = 0
        if zag:
            self.dir = -1 if zag.x < self.x else 1
            self._update_sprite_flip()
        self.movement.xdir = 0
        self.movement.ydir = 0

    def _update_gun_attack(self, zag):
        dt = game_framework.frame_time
        self.anim_timer += dt
        if self.anim_timer >= GUN_ANIM_SPEED:
            self.anim_timer -= GUN_ANIM_SPEED
            self.frame += 1
            if self.frame >= GUN_FRAME_COUNT:
                self.state = "idle"
                self._set_animation(self.idle_image, IDLE_FRAME_W, IDLE_FRAME_H)
                self.frame = IDLE_ANIM_PATTERN[self.anim_index % len(IDLE_ANIM_PATTERN)]
                return

        if self.frame == GUN_FRAME_COUNT - 1 and not self.attack_fired:
            self.attack_fired = True
            if zag:
                direction = (zag.x - self.x, zag.y - self.y)
            else:
                direction = (-1, 0) if self.dir < 0 else (1, 0)
            missile = MissileProjectile(
                self.x + self.dir * 30,
                self.y + 10,
                direction,
                self.missile_image,
                damage=MISSILE_DAMAGE,
            )
            game_world.add_object(missile)

    def _can_backrun(self):
        # Allow the backrun unless the boss is already too high, where another jump
        # would be ineffective.
        return not self._prefer_bombs_only()

    def _start_backrun(self):
        self.state = "backrun"
        self._set_animation(self.back_image, BACKRUN_FRAME_W, BACKRUN_FRAME_H)
        self.backrun_timer = 0.0
        self.vertical_velocity = BACKRUN_JUMP_VY
        canvas_mid_x = get_canvas_width() * 0.5
        self.movement.xdir = 1 if self.transform.x < canvas_mid_x else -1
        self.movement.speed = BACKRUN_SPEED

    def _update_backrun(self, zag):
        dt = game_framework.frame_time
        self.backrun_timer += dt
        self.anim_timer += dt
        if self.anim_timer >= GUN_ANIM_SPEED:
            self.anim_timer -= GUN_ANIM_SPEED
            self.frame = (self.frame + 1) % BACKRUN_FRAME_COUNT

        self.vertical_velocity += BOMB_FLIGHT_GRAVITY * 0.35 * dt
        self.transform.y += self.vertical_velocity * dt
        if self.transform.y < BACKRUN_FRAME_H * SCALE:
            self.transform.y = BACKRUN_FRAME_H * SCALE
            self.vertical_velocity = 0.0

        if self.backrun_timer >= BACKRUN_DURATION:
            self.state = "idle"
            self._set_animation(self.idle_image, IDLE_FRAME_W, IDLE_FRAME_H)
            self.frame = IDLE_ANIM_PATTERN[self.anim_index % len(IDLE_ANIM_PATTERN)]
            self.movement.xdir = 0
            self.movement.speed = self.base_speed
            self.vertical_velocity = 0.0

    def _restore_animation_for_state(self):
        if self.state == "idle":
            self._set_animation(self.idle_image, IDLE_FRAME_W, IDLE_FRAME_H)
            self.frame = IDLE_ANIM_PATTERN[self.anim_index % len(IDLE_ANIM_PATTERN)]
        elif self.state == "bomb_attack":
            self._set_animation(self.bomb_image, BOMB_FRAME_W, BOMB_FRAME_H)
        elif self.state == "gun_attack":
            self._set_animation(self.gun_image, GUN_FRAME_W, GUN_FRAME_H)
        elif self.state == "backrun":
            self._set_animation(self.back_image, BACKRUN_FRAME_W, BACKRUN_FRAME_H)
        elif self.state == "hit":
            self._set_animation(self.hit_image, IDLE_FRAME_W, IDLE_FRAME_H)

    def handle_collision(self, other):
        if getattr(other, "collision_group", None) == CollisionGroup.PROJECTILE:
            self._enter_hit(other)
        elif getattr(other, "collision_group", None) == CollisionGroup.PLAYER:
            combat = getattr(other, "combat", None)
            if combat:
                combat.take_damage(12)

    def _enter_hit(self, attacker=None):
        if self.hit_timer > 0:
            return
        self.prev_state = self.state if self.state != "hit" else self.prev_state
        self.state = "hit"
        self.hit_timer = HIT_DURATION
        self._set_animation(self.hit_image, IDLE_FRAME_W, IDLE_FRAME_H)
        self.frame = 0

        if attacker and hasattr(attacker, "transform"):
            knock_dir = 1 if attacker.transform.x < self.transform.x else -1
        else:
            knock_dir = -self.dir
        self.transform.x += knock_dir * 18
        self.transform.y += 6

