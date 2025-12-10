import math

from pico2d import get_canvas_height, get_canvas_width

import game_framework
import game_world
from collision_manager import CollisionGroup
from components.component_collision import CollisionComponent
from components.component_combat import CombatComponent
from components.component_move import MovementComponent, MovementType
from components.component_render import RenderComponent
from components.component_sprite import SpriteComponent
from components.component_transform import TransformComponent
from game_object import GameObject


DEFAULT_KNOCKBACK_Y = 300


class Projectile(GameObject):
    def __init__(
        self,
        x,
        y,
        direction,
        speed,
        damage,
        width,
        height,
        image=None,
        knockback_x=140,
        knockback_y=DEFAULT_KNOCKBACK_Y,
        collision_mask=CollisionGroup.MONSTER,
    ):
        super().__init__()
        self.collision_group = CollisionGroup.PROJECTILE
        self.damage = damage
        self.knockback_x = knockback_x
        self.knockback_y = knockback_y

        self.transform = self.add_component(TransformComponent(x, y, width, height))
        self.movement = self.add_component(MovementComponent(speed))
        self.movement.type = None
        self.collision = self.add_component(
            CollisionComponent(
                group=CollisionGroup.PROJECTILE,
                mask=collision_mask,
                width=width,
                height=height,
            )
        )
        self.render = None

        if image:
            self.render = self.add_component(RenderComponent(image, width, height))

        self.set_direction(direction)

    def set_direction(self, direction):
        dx, dy = direction
        if dx == 0 and dy == 0:
            angle = 0.0
        else:
            angle = math.atan2(dy, dx)

        self.movement.xdir = math.cos(angle)
        self.movement.ydir = math.sin(angle)

        if self.render:
            self.render.rotation = angle

    def _apply_knockback(self, other):
        other_transform = getattr(other, "transform", None)
        if other_transform:
            other_transform.y -= 10
            return

        other_move = other.get(MovementComponent) if hasattr(other, "get") else None
        if other_move:
            other_move.ydir -= 10

    def handle_collision(self, other):
        if getattr(other, "collision_group", None) == CollisionGroup.PROJECTILE:
            return

        combat = other.get(CombatComponent) if hasattr(other, "get") else None
        if combat:
            combat.take_damage(self.damage)
        elif hasattr(other, "take_damage"):
            other.take_damage(self.damage)

        self._apply_knockback(other)
        game_world.remove_object(self)

    def update(self):
        dt = game_framework.frame_time
        if self.movement:
            self.transform.x += self.movement.xdir * self.movement.speed * dt
            self.transform.y += self.movement.ydir * self.movement.speed * dt

        super().update()

        if self.movement and self.movement.type == MovementType.DIRECTIONAL:
            cw = get_canvas_width()
            world_height = get_canvas_height() * 2
            if (
                self.transform.x < -self.transform.w
                or self.transform.x > cw + self.transform.w
                or self.transform.y < -self.transform.h
                or self.transform.y > world_height + self.transform.h
            ):
                game_world.remove_object(self)


class ExplosionEffect(GameObject):
    def __init__(self, x, y, images, interval=0.05):
        super().__init__()
        self.images = images
        self.interval = interval
        self.timer = 0.0
        self.index = 0

        max_w = max(img.w for img in images)
        max_h = max(img.h for img in images)

        self.transform = self.add_component(TransformComponent(x, y, max_w, max_h))
        self.sprite = self.add_component(SpriteComponent(images[0], images[0].w, images[0].h))

    def update(self, target=None):
        dt = game_framework.frame_time
        self.timer += dt
        if self.timer >= self.interval:
            self.timer -= self.interval
            self.index += 1
            if self.index >= len(self.images):
                game_world.remove_object(self)
                return
            self.sprite.image = self.images[self.index]
            self.sprite.frame_w = self.sprite.image.w
            self.sprite.frame_h = self.sprite.image.h

        from game_object import GameObject

        GameObject.update(self)


class BombProjectile(Projectile):
    def __init__(
        self,
        x,
        y,
        target,
        image,
        explosion_images,
        damage,
        gravity=-1200.0,
        lifetime=3.0,
        detonate_distance=40.0,
    ):
        target_pos = (target.transform.x, target.transform.y) if hasattr(target, "transform") else target
        dx = target_pos[0] - x
        dy = target_pos[1] - y

        self.gravity = gravity
        self.target = target
        self.target_pos = target_pos
        self.lifetime = 0.0
        self.max_lifetime = lifetime
        self.detonate_distance_sq = detonate_distance * detonate_distance
        self.explosion_images = explosion_images
        self.exploded = False
        self.explosion_duration = 0.2
        self.explosion_timer = 0.0
        self.damaged_targets = set()

        self.explosion_width = max((img.w for img in explosion_images), default=40)
        self.explosion_height = max((img.h for img in explosion_images), default=44)

        self.flight_time = max(0.5, min(1.2, abs(dx) / 200.0 + 0.6))
        vx = dx / self.flight_time
        vy = dy / self.flight_time - 0.5 * gravity * self.flight_time

        width, height = 40, 44
        super().__init__(
            x,
            y,
            (1, 0),
            speed=0,
            damage=damage,
            width=width,
            height=height,
            image=image,
            knockback_x=280,
            knockback_y=600,
            collision_mask=CollisionGroup.PLAYER,
        )
        self.vx = vx
        self.vy = vy
        self.movement.xdir = 1 if self.vx >= 0 else -1

    def _apply_explosion_damage(self, target=None):
        if not target or target in self.damaged_targets:
            return

        combat = target.get(CombatComponent) if hasattr(target, "get") else None
        if combat:
            combat.take_damage(self.damage)
        elif hasattr(target, "take_damage"):
            target.take_damage(self.damage)

        if hasattr(target, "transform"):
            target.transform.y -= 10

        self.damaged_targets.add(target)

    def _explode(self, target=None):
        if self.exploded:
            return
        self.exploded = True
        self.explosion_timer = 0.0

        self.transform.w = self.explosion_width
        self.transform.h = self.explosion_height
        self.collision.override_width = self.explosion_width
        self.collision.override_height = self.explosion_height

        self.vx = 0
        self.vy = 0
        self.movement.xdir = 0
        self.movement.ydir = 0

        game_world.add_object(ExplosionEffect(self.transform.x, self.transform.y, self.explosion_images), depth=1)
        self._apply_explosion_damage(target)

    def update(self, target=None):
        dt = game_framework.frame_time
        if self.exploded:
            self.explosion_timer += dt
            if self.explosion_timer >= self.explosion_duration:
                game_world.remove_object(self)
                return

            super().update()
            return

        target = target or self.target

        self.lifetime += dt

        self.vy += self.gravity * dt
        self.transform.x += self.vx * dt
        self.transform.y += self.vy * dt

        cw = get_canvas_width()
        ch = get_canvas_height()
        world_h = ch * 2
        if (
            self.transform.x < -self.transform.w
            or self.transform.x > cw + self.transform.w
            or self.transform.y < -self.transform.h
            or self.transform.y > world_h + self.transform.h
        ):
            game_world.remove_object(self)
            return

        dx = self.target_pos[0] - self.transform.x
        dy = self.target_pos[1] - self.transform.y
        if dx * dx + dy * dy <= self.detonate_distance_sq:
            if target and hasattr(target, "transform"):
                tx = target.transform.x - self.transform.x
                ty = target.transform.y - self.transform.y
                if tx * tx + ty * ty <= self.detonate_distance_sq:
                    self._explode(target)
                    return
            self._explode()
            return

        if self.lifetime >= self.max_lifetime:
            self._explode()
            return

        super().update()

    def handle_collision(self, other):
        if getattr(other, "collision_group", None) == CollisionGroup.PLAYER:
            if self.exploded:
                self._apply_explosion_damage(other)
            else:
                self._explode(other)


class MissileProjectile(Projectile):
    def __init__(self, x, y, direction, image, damage):
        super().__init__(
            x,
            y,
            direction,
            speed=420.0,
            damage=damage,
            width=18,
            height=18,
            image=image,
            knockback_x=90,
            knockback_y=150,
            collision_mask=CollisionGroup.PLAYER,
        )

    def handle_collision(self, other):
        self.knockback_y = 150
        super().handle_collision(other)

    def update(self):
        super().update()
