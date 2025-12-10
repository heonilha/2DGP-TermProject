import math
import os
import random

from pico2d import get_canvas_width, load_image

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

# Sprite and animation settings
IDLE_FRAME_W = 47
IDLE_FRAME_H = 71
IDLE_FRAMES = [0, 1, 2, 1]
IDLE_ANIM_SPEED = 0.15

HIT_FRAME_W = 47
HIT_FRAME_H = 71
HIT_DURATION = 0.18
HIT_KNOCKBACK = 140.0
INVINCIBLE_DURATION = 0.35

ATTACK_FRAME_W = 64
ATTACK_FRAME_H = 64
ATTACK_FRAME_COUNT = 6
ATTACK_ANIM_SPEED = 0.11
ATTACK_COOLDOWN = 1.4
BOMB_DAMAGE = 18
MISSILE_DAMAGE = 14

BACKRUN_FRAME_W = 47
BACKRUN_FRAME_H = 71
BACKRUN_FRAMES = [0, 1, 2, 3, 4]
BACKRUN_ANIM_SPEED = 0.12
BACKRUN_DISTANCE = 240.0
BACKRUN_HEIGHT = 120.0
BACKRUN_DURATION = 0.75
BACKRUN_TRIGGER_RANGE = 90.0

BOMB_ARC_DISTANCE = 260.0
BOMB_ARC_HEIGHT = 180.0
BOMB_ARC_DURATION = 0.95

MISSILE_SPEED = 480.0
PROJECTILE_SIZE = 48

SCALE = 2.5
COLLISION_SCALE = 0.9


def apply_knockback(target, dx, dy=0.0):
    tr = target.get(TransformComponent) if hasattr(target, "get") else None
    if not tr:
        return
    tr.x += dx
    tr.y += dy
    tr.x = max(20, min(get_canvas_width() - 20, tr.x))


class BombProjectile(GameObject):
    def __init__(self, start_pos, target_pos, height, duration, face_dir):
        super().__init__()
        base_dir = os.path.dirname(os.path.dirname(__file__))
        bomb_path = os.path.join(base_dir, "resource", "Image", "Monster", "bomb.png")
        if not os.path.exists(bomb_path):
            raise FileNotFoundError("bomb.png not found for BombProjectile")

        self.collision_group = CollisionGroup.PROJECTILE

        self.transform = self.add_component(
            TransformComponent(start_pos[0], start_pos[1], PROJECTILE_SIZE, PROJECTILE_SIZE)
        )
        self.sprite = self.add_component(SpriteComponent(load_image(bomb_path), PROJECTILE_SIZE, PROJECTILE_SIZE))
        self.movement = self.add_component(MovementComponent(speed=0))
        self.collision = self.add_component(
            CollisionComponent(
                group=CollisionGroup.PROJECTILE,
                mask=CollisionGroup.PLAYER,
                width=PROJECTILE_SIZE * 0.8,
                height=PROJECTILE_SIZE * 0.8,
            )
        )
        self.projectile = self.add_component(ProjectileComponent(BOMB_DAMAGE))

        end_x = start_pos[0] + face_dir * BOMB_ARC_DISTANCE
        end_y = target_pos[1]
        self.movement.start_parabolic(start_pos, (end_x, end_y), height, duration, self._explode)

    @property
    def x(self):
        return self.transform.x

    @property
    def y(self):
        return self.transform.y

    def _explode(self):
        explosion = BombExplosion(self.x, self.y)
        game_world.add_object(explosion, depth=1)
        game_world.remove_object(self)

    def handle_collision(self, other):
        if getattr(other, "collision_group", None) == CollisionGroup.PLAYER:
            self.projectile.on_hit(other)
            self._explode()


class MissileProjectile(GameObject):
    def __init__(self, x, y, face_dir):
        super().__init__()
        self.face_dir = face_dir
        base_dir = os.path.dirname(os.path.dirname(__file__))
        missile_path = os.path.join(base_dir, "resource", "Image", "Monster", "GoblinKingMissile.png")
        if not os.path.exists(missile_path):
            raise FileNotFoundError("GoblinKingMissile.png not found for MissileProjectile")

        self.collision_group = CollisionGroup.PROJECTILE

        self.transform = self.add_component(TransformComponent(x, y, PROJECTILE_SIZE, PROJECTILE_SIZE))
        self.sprite = self.add_component(SpriteComponent(load_image(missile_path), ATTACK_FRAME_W, ATTACK_FRAME_H))
        self.sprite.frame = 0
        self.movement = self.add_component(MovementComponent(MISSILE_SPEED))
        self.movement.xdir = face_dir
        self.collision = self.add_component(
            CollisionComponent(
                group=CollisionGroup.PROJECTILE,
                mask=CollisionGroup.PLAYER,
                width=PROJECTILE_SIZE * 0.7,
                height=PROJECTILE_SIZE * 0.7,
            )
        )
        self.projectile = self.add_component(ProjectileComponent(MISSILE_DAMAGE))
        self.anim_timer = 0.0

    def update(self):
        dt = game_framework.frame_time
        self.anim_timer += dt
        if self.anim_timer >= ATTACK_ANIM_SPEED:
            self.anim_timer -= ATTACK_ANIM_SPEED
            self.sprite.frame = (self.sprite.frame + 1) % ATTACK_FRAME_COUNT

        super().update()

        # Remove if out of screen bounds
        if self.transform.x < -100 or self.transform.x > get_canvas_width() + 100:
            game_world.remove_object(self)

    def handle_collision(self, other):
        if getattr(other, "collision_group", None) == CollisionGroup.PLAYER:
            self.projectile.on_hit(other)
            apply_knockback(other, self.face_dir * 120, 30)
            game_world.remove_object(self)


class BombExplosion(GameObject):
    def __init__(self, x, y):
        super().__init__()
        base_dir = os.path.dirname(os.path.dirname(__file__))
        sheet_paths = [
            os.path.join(base_dir, "resource", "Image", "Monster", "hit_4x4_1.png"),
            os.path.join(base_dir, "resource", "Image", "Monster", "hit_4x4_2.png"),
            os.path.join(base_dir, "resource", "Image", "Monster", "hit_4x4_3.png"),
        ]
        self.images = [load_image(path) for path in sheet_paths]
        self.sheet_index = 0
        self.frame_index = 0
        self.frames_per_sheet = 16
        self.anim_timer = 0.0
        self.anim_speed = 0.03

        # Calculate frame sizes dynamically
        frame_w = self.images[0].w // 4
        frame_h = self.images[0].h // 4

        self.transform = self.add_component(TransformComponent(x, y, frame_w * 2, frame_h * 2))
        self.sprite = self.add_component(SpriteComponent(self.images[0], frame_w, frame_h))
        self.collision_group = CollisionGroup.PROJECTILE
        self.collision = self.add_component(
            CollisionComponent(
                group=CollisionGroup.PROJECTILE,
                mask=CollisionGroup.PLAYER | CollisionGroup.MONSTER,
                width=frame_w * 1.6,
                height=frame_h * 1.6,
            )
        )
        self.projectile = self.add_component(ProjectileComponent(BOMB_DAMAGE))

    def update(self):
        dt = game_framework.frame_time
        self.anim_timer += dt
        if self.anim_timer >= self.anim_speed:
            self.anim_timer -= self.anim_speed
            self.frame_index += 1
            if self.frame_index >= self.frames_per_sheet:
                self.frame_index = 0
                self.sheet_index += 1
                if self.sheet_index >= len(self.images):
                    game_world.remove_object(self)
                    return
                self.sprite.image = self.images[self.sheet_index]
            self.sprite.frame = self.frame_index

        super().update()

    def handle_collision(self, other):
        group = getattr(other, "collision_group", None)
        if group in (CollisionGroup.PLAYER, CollisionGroup.MONSTER):
            self.projectile.on_hit(other)
            self._apply_knockback(other)

    @staticmethod
    def _apply_knockback(target):
        direction = -1 if getattr(target, "face_dir", 1) > 0 else 1
        apply_knockback(target, direction * 80, 40)


class GoblinKing(GameObject):
    def __init__(self, spawn_pos=None):
        super().__init__()

        base_dir = os.path.dirname(os.path.dirname(__file__))
        idle_path = os.path.join(base_dir, "resource", "Image", "Monster", "GoblinKingIdle.png")
        hit_path = os.path.join(base_dir, "resource", "Image", "Monster", "Goblin KingHit.png")
        bomb_attack_path = os.path.join(base_dir, "resource", "Image", "Monster", "GoblinKing Att.png")
        missile_attack_path = os.path.join(base_dir, "resource", "Image", "Monster", "GoblinKingMissile.png")
        backrun_path = os.path.join(base_dir, "resource", "Image", "Monster", "GoblinKing BackRun.png")

        for path in [idle_path, hit_path, bomb_attack_path, missile_attack_path, backrun_path]:
            if not os.path.exists(path):
                raise FileNotFoundError(f"Missing GoblinKing resource: {path}")

        if spawn_pos is None:
            start_x = random.randint(200, max(210, get_canvas_width() - 200))
            start_y = random.randint(220, 520)
        elif isinstance(spawn_pos, dict):
            start_x = spawn_pos.get("x", random.randint(200, max(210, get_canvas_width() - 200)))
            start_y = spawn_pos.get("y", random.randint(220, 520))
        else:
            start_x, start_y = spawn_pos

        self.transform = self.add_component(
            TransformComponent(start_x, start_y, IDLE_FRAME_W * SCALE, IDLE_FRAME_H * SCALE)
        )
        self.sprite = self.add_component(SpriteComponent(load_image(idle_path), IDLE_FRAME_W, IDLE_FRAME_H))
        self.idle_image = self.sprite.image
        self.hit_image = load_image(hit_path)
        self.bomb_attack_image = load_image(bomb_attack_path)
        self.missile_attack_image = load_image(missile_attack_path)
        self.backrun_image = load_image(backrun_path)

        self.collision_group = CollisionGroup.MONSTER
        self.collision = self.add_component(
            CollisionComponent(
                group=CollisionGroup.MONSTER,
                mask=CollisionGroup.PLAYER | CollisionGroup.PROJECTILE,
                width=self.transform.w * COLLISION_SCALE,
                height=self.transform.h * COLLISION_SCALE,
            )
        )
        self.combat = self.add_component(CombatComponent(120, INVINCIBLE_DURATION, enable_invincibility=True))
        self.movement = self.add_component(MovementComponent(120))
        self.perception = self.add_component(PerceptionComponent())
        self.hud = self.add_component(HUDComponent(hp_width=90, hp_height=10, hp_offset=90))

        self.face_dir = -1
        self._update_sprite_flip()

        self.state = "idle"
        self.prev_state = "idle"
        self.anim_timer = 0.0
        self.frame_index = 0
        self.frame_sequence = IDLE_FRAMES

        self.hit_timer = 0.0
        self.attack_timer = 0.0
        self.attack_cooldown = ATTACK_COOLDOWN
        self.has_spawned_projectile = False

    @property
    def x(self):
        return self.transform.x

    @property
    def y(self):
        return self.transform.y

    @property
    def hp(self):
        return self.combat.hp

    def _update_sprite_flip(self):
        if self.sprite:
            self.sprite.flip = "" if self.face_dir < 0 else "h"

    def _set_animation(self, image, frame_w, frame_h, frames):
        self.sprite.image = image
        self.sprite.frame_w = frame_w
        self.sprite.frame_h = frame_h
        self.frame_sequence = frames
        self.frame_index = 0
        self.sprite.frame = self.frame_sequence[self.frame_index]

    def update(self, target=None):
        if self.hp <= 0:
            game_world.remove_object(self)
            return

        self.perception.target = target

        if self.state == "idle":
            self._update_idle()
        elif self.state == "hit":
            self._update_hit()
        elif self.state == "bomb_attack":
            self._update_attack(attack_type="bomb")
        elif self.state == "missile_attack":
            self._update_attack(attack_type="missile")
        elif self.state == "backrun":
            self._update_backrun()

        super().update()

    def _update_idle(self):
        dt = game_framework.frame_time
        self.movement.xdir = 0
        self.anim_timer += dt
        if self.anim_timer >= IDLE_ANIM_SPEED:
            self.anim_timer -= IDLE_ANIM_SPEED
            self.frame_index = (self.frame_index + 1) % len(IDLE_FRAMES)
            self.sprite.frame = IDLE_FRAMES[self.frame_index]

        self.attack_cooldown = min(ATTACK_COOLDOWN, self.attack_cooldown + dt)

        target = self.perception.target
        if not target:
            return

        dx = target.x - self.x
        dy = target.y - self.y
        distance = math.hypot(dx, dy)
        self.face_dir = -1 if dx < 0 else 1
        self._update_sprite_flip()

        if distance < BACKRUN_TRIGGER_RANGE:
            if self._has_backrun_space():
                self._start_backrun()
            elif self.attack_cooldown >= ATTACK_COOLDOWN:
                self._start_attack("bomb")
        elif self.attack_cooldown >= ATTACK_COOLDOWN and distance < 420:
            self._start_attack(random.choice(["bomb", "missile"]))

    def _has_backrun_space(self):
        margin = 80
        target_x = self.x - self.face_dir * BACKRUN_DISTANCE
        return margin < target_x < get_canvas_width() - margin

    def _start_backrun(self):
        self.state = "backrun"
        self._set_animation(self.backrun_image, BACKRUN_FRAME_W, BACKRUN_FRAME_H, BACKRUN_FRAMES)
        self.anim_timer = 0.0
        self.movement.start_parabolic(
            (self.x, self.y),
            (self.x - self.face_dir * BACKRUN_DISTANCE, self.y),
            BACKRUN_HEIGHT,
            BACKRUN_DURATION,
            self._end_backrun,
        )

    def _end_backrun(self):
        if self.state == "backrun":
            self.state = "idle"
            self._set_animation(self.idle_image, IDLE_FRAME_W, IDLE_FRAME_H, IDLE_FRAMES)
            self.frame_index = 0

    def _start_attack(self, attack_type):
        if attack_type == "bomb":
            self.state = "bomb_attack"
            self._set_animation(self.bomb_attack_image, ATTACK_FRAME_W, ATTACK_FRAME_H, list(range(ATTACK_FRAME_COUNT)))
        else:
            self.state = "missile_attack"
            self._set_animation(
                self.missile_attack_image, ATTACK_FRAME_W, ATTACK_FRAME_H, list(range(ATTACK_FRAME_COUNT))
            )
        self.anim_timer = 0.0
        self.attack_timer = 0.0
        self.has_spawned_projectile = False
        self.attack_cooldown = 0.0
        self.movement.xdir = 0

    def _update_attack(self, attack_type):
        dt = game_framework.frame_time
        self.attack_timer += dt
        if self.attack_timer >= ATTACK_ANIM_SPEED:
            self.attack_timer -= ATTACK_ANIM_SPEED
            self.frame_index += 1
            if self.frame_index >= len(self.frame_sequence):
                self.state = "idle"
                self._set_animation(self.idle_image, IDLE_FRAME_W, IDLE_FRAME_H, IDLE_FRAMES)
                self.frame_index = 0
                return
            self.sprite.frame = self.frame_sequence[self.frame_index]

        # Spawn projectile at last frame once
        if not self.has_spawned_projectile and self.frame_index == len(self.frame_sequence) - 1:
            if attack_type == "bomb":
                bomb = BombProjectile(
                    (self.x, self.y),
                    (self.x + self.face_dir * BOMB_ARC_DISTANCE, self.y - 60),
                    BOMB_ARC_HEIGHT,
                    BOMB_ARC_DURATION,
                    self.face_dir,
                )
                game_world.add_object(bomb, depth=1)
            else:
                missile = MissileProjectile(self.x + self.face_dir * 40, self.y, self.face_dir)
                game_world.add_object(missile, depth=1)
            self.has_spawned_projectile = True

    def _start_hit(self, knockback_dir):
        if self.state == "hit":
            return
        self.prev_state = self.state
        self.state = "hit"
        self.hit_timer = HIT_DURATION
        self._set_animation(self.hit_image, HIT_FRAME_W, HIT_FRAME_H, [0])
        if self.movement:
            self.movement.type = MovementType.DIRECTIONAL
            if hasattr(self.movement, "_reset_path"):
                self.movement._reset_path()
        self._apply_knockback(knockback_dir)

    def _apply_knockback(self, direction):
        self.transform.x += direction * HIT_KNOCKBACK
        self.transform.x = max(40, min(get_canvas_width() - 40, self.transform.x))

    def _update_hit(self):
        dt = game_framework.frame_time
        self.hit_timer -= dt
        if self.hit_timer <= 0:
            self.state = "idle"
            self._set_animation(self.idle_image, IDLE_FRAME_W, IDLE_FRAME_H, IDLE_FRAMES)
            self.frame_index = 0

    def handle_collision(self, other):
        group = getattr(other, "collision_group", None)
        if group == CollisionGroup.PROJECTILE:
            prev_hp = self.hp
            combat = self.get(CombatComponent)
            if combat:
                proj_comp = other.get(ProjectileComponent) if hasattr(other, "get") else None
                damage = proj_comp.damage if proj_comp else 10
                combat.take_damage(damage)
            if self.hp < prev_hp:
                direction = -1 if getattr(other, "face_dir", self.face_dir) > 0 else 1
                self._start_hit(direction)
        elif group == CollisionGroup.PLAYER:
            self._start_hit(1 if self.face_dir < 0 else -1)
