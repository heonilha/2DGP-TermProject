import game_framework
import game_world

from components.component_base import Component
from components.component_transform import TransformComponent


class AttackComponent(Component):
    def __init__(self, attack_image, duration=0.2, damage=5, width=64, height=64, offset_x=32, offset_y=0, scale=1.0):
        super().__init__()
        if isinstance(attack_image, (list, tuple)):
            self.attack_images = list(attack_image)
        else:
            self.attack_images = [attack_image]
        self.attack_duration = duration
        self.attack_timer = 0.0
        self.damage = damage
        self.hit_monsters = []
        self.base_width = width
        self.base_height = height
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.scale = scale
        self.active = False
        self.attack_dir = 1

    def _attack_progress(self):
        return max(0.0, min(1.0, (self.attack_duration - self.attack_timer) / self.attack_duration))

    def _get_frame_index(self):
        return min(len(self.attack_images) - 1, int(self._attack_progress() * len(self.attack_images)))

    def _get_frame_size(self, attack_image):
        source_w = max(1, int(getattr(attack_image, 'w', self.base_width)))
        source_h = max(1, int(getattr(attack_image, 'h', self.base_height)))
        dest_w = max(1, int(source_w * self.scale))
        dest_h = max(1, int(source_h * self.scale))
        return source_w, source_h, dest_w, dest_h

    def start_attack(self, face_dir):
        self.attack_timer = self.attack_duration
        self.hit_monsters.clear()
        self.active = True
        self.attack_dir = face_dir
        if hasattr(self.owner, 'attack_cooldown'):
            self.owner.attack_cooldown_timer = self.owner.attack_cooldown

    def is_attacking(self):
        return self.active and self.attack_timer > 0

    def update(self):
        if not self.is_attacking():
            return

        self.attack_timer -= game_framework.frame_time

        if 0.1 < self.attack_timer < 0.2:
            self.check_attack_collision()

        if self.attack_timer <= 0:
            self.active = False

    def draw(self):
        if not self.is_attacking() or not self.attack_images:
            return

        tr = self.owner.get(TransformComponent)
        if not tr:
            return

        frame_index = self._get_frame_index()
        attack_image = self.attack_images[frame_index]
        source_w, source_h, dest_w, dest_h = self._get_frame_size(attack_image)

        flip = 'h' if self.attack_dir == 1 else ''
        base_x = tr.x + (self.offset_x if self.attack_dir == 1 else -self.offset_x)

        attack_image.clip_composite_draw(
            0,
            0,
            source_w,
            source_h,
            0,
            flip,
            base_x,
            tr.y,
            dest_w,
            dest_h,
        )

    def check_attack_collision(self):
        tr = self.owner.get(TransformComponent)
        if not tr:
            return

        frame_index = self._get_frame_index()
        attack_image = self.attack_images[frame_index]
        _, _, dest_w, dest_h = self._get_frame_size(attack_image)

        attack_box_x = tr.x + (self.offset_x if self.attack_dir == 1 else -self.offset_x)
        attack_box_y = tr.y + self.offset_y
        half_w = dest_w * 0.5
        half_h = dest_h * 0.5
        attack_bb = (
            attack_box_x - half_w,
            attack_box_y - half_h,
            attack_box_x + half_w,
            attack_box_y + half_h,
        )

        for target in game_world.all_objects():
            if target == self.owner:
                continue
            if hasattr(target, 'get_bb') and target not in self.hit_monsters:
                target_bb = target.get_bb()
                if (
                    attack_bb[0] < target_bb[2]
                    and attack_bb[2] > target_bb[0]
                    and attack_bb[1] < target_bb[3]
                    and attack_bb[3] > target_bb[1]
                ):
                    if hasattr(target, 'take_damage'):
                        target.take_damage(self.damage)
                    self.hit_monsters.append(target)
