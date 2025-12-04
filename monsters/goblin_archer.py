import math
import os
import random

from pico2d import get_canvas_height, get_canvas_width, load_image

import game_framework
import game_world
from collision_manager import CollisionGroup
from components.component_combat import CombatComponent
from components.component_collision import CollisionComponent
from components.component_hud import HUDComponent
from components.component_move import MovementComponent
from components.component_perception import PerceptionComponent
from components.component_projectile import ProjectileComponent
from components.component_sprite import SpriteComponent
from components.component_transform import TransformComponent
from game_object import GameObject

FRAME_W = 26  # 182 / 7
FRAME_H = 33
FRAME_COUNT = 7
SCALE = 2

MOVE_ANIM_SPEED = 0.12
PREPARE_TIME = 1.0
ATTACK_ANIM_DURATION = 0.45
ATTACK_FIRE_TIME = 0.2
ATTACK_COOLDOWN = 2.2
ATTACK_DAMAGE = 10

DETECTION_RANGE = 320
PATROL_RADIUS = 160
ARROW_SPEED = 280
ARROW_SIZE = (40, 10)


class Arrow(GameObject):
    _arrow_image = None

    def __init__(self, x, y, direction):
        super().__init__()

        if Arrow._arrow_image is None:
            base_dir = os.path.dirname(os.path.dirname(__file__))
            image_path = os.path.join(base_dir, "resource", "Image", "Projectile", "arrow.png")
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Arrow image not found: `{image_path}`")
            Arrow._arrow_image = load_image(image_path)

        self.collision_group = CollisionGroup.MONSTER

        width, height = ARROW_SIZE
        self.transform = self.add_component(TransformComponent(x, y, width, height))
        self.movement = self.add_component(MovementComponent(ARROW_SPEED))
        self.collision = self.add_component(
            CollisionComponent(
                group=CollisionGroup.MONSTER,
                mask=CollisionGroup.PLAYER,
                width=width,
                height=height,
            )
        )
        self.projectile = self.add_component(ProjectileComponent(ATTACK_DAMAGE))
        self.sprite = self.add_component(
            SpriteComponent(Arrow._arrow_image, Arrow._arrow_image.w, Arrow._arrow_image.h)
        )

        self.set_direction(direction)

    def set_direction(self, direction):
        dx, dy = direction
        length = math.sqrt(dx * dx + dy * dy)
        if length == 0:
            self.movement.xdir = 1
            self.movement.ydir = 0
            return
        self.movement.xdir = dx / length
        self.movement.ydir = dy / length

        if self.sprite:
            # Arrow art faces left by default, so flip when traveling right.
            self.sprite.flip = "h" if self.movement.xdir >= 0 else ""

    def handle_collision(self, other):
        if getattr(other, "collision_group", None) == CollisionGroup.PLAYER:
            self.projectile.on_hit(other)

    def update(self):
        super().update()
        if (
            self.transform.x < -50
            or self.transform.x > get_canvas_width() + 50
            or self.transform.y < -50
            or self.transform.y > get_canvas_height() + 50
        ):
            game_world.remove_object(self)


class GoblinArcher(GameObject):
    def __init__(self):
        super().__init__()

        base_dir = os.path.dirname(os.path.dirname(__file__))
        image_path = os.path.join(base_dir, "resource", "Image", "Monster", "Goblin Archer.png")
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: `{image_path}`")

        start_x = random.randint(140, max(150, get_canvas_width() - 140))
        start_y = random.randint(140, 420)

        self.transform = self.add_component(
            TransformComponent(start_x, start_y, FRAME_W * SCALE, FRAME_H * SCALE)
        )
        self.sprite = self.add_component(SpriteComponent(load_image(image_path), FRAME_W, FRAME_H))
        self.collision_group = CollisionGroup.MONSTER
        self.base_collision_w = self.transform.w - 8
        self.collision = self.add_component(
            CollisionComponent(
                group=CollisionGroup.MONSTER,
                mask=CollisionGroup.PLAYER | CollisionGroup.PROJECTILE,
                width=self.base_collision_w,
                height=self.transform.h - 8,
            )
        )
        self.combat = self.add_component(CombatComponent(24))
        self.movement = self.add_component(MovementComponent(80))
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
        self.cooldown_timer = ATTACK_COOLDOWN
        self.arrow_fired = False

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
            self.sprite.flip = "h" if self.dir < 0 else ""

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
        self.cooldown_timer = 0.0
        self.arrow_fired = False

    def _update_attack(self):
        dt = game_framework.frame_time
        self.attack_anim_timer += dt

        progress = min(1.0, self.attack_anim_timer / ATTACK_ANIM_DURATION)
        frame_index = 4 + int(progress * 3)
        self.frame = min(frame_index, 6)

        if (not self.arrow_fired) and self.attack_anim_timer >= ATTACK_FIRE_TIME:
            self._fire_arrow()
            self.arrow_fired = True

        if self.attack_anim_timer >= ATTACK_ANIM_DURATION:
            self.state = "cooldown"
            self.frame = 0

    def _fire_arrow(self):
        target = self.perception.target
        if target:
            dx = target.x - self.x
            dy = target.y - self.y
        else:
            dx, dy = self.dir, 0

        arrow = Arrow(self.x + self.dir * (self.transform.w * 0.4), self.y, (dx, dy))
        game_world.add_object(arrow, 1)

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
