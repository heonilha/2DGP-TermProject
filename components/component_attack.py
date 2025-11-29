import game_framework
import game_world

from components.component_base import Component
from components.component_transform import TransformComponent


class AttackComponent(Component):
    def __init__(self, attack_image, duration=0.2, damage=5, width=64, height=64, offset_x=32, offset_y=0):
        super().__init__()
        self.attack_image = attack_image
        self.attack_duration = duration
        self.attack_timer = 0.0
        self.damage = damage
        self.hit_monsters = []
        self.width = width
        self.height = height
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.active = False
        self.attack_dir = 1

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
        if not self.is_attacking() or not self.attack_image:
            return

        tr = self.owner.get(TransformComponent)
        if not tr:
            return

        src_w, src_h = 114, 217
        dest_w, dest_h = 32, 64
        slices = 6
        slice_h_src = src_h // slices
        slice_h_dest = dest_h / slices

        progress = max(0.0, min(1.0, (self.attack_duration - self.attack_timer) / self.attack_duration))
        slices_to_draw = int(progress * slices)

        flip = 'h' if self.attack_dir == 1 else ''
        base_x = tr.x + (self.offset_x if self.attack_dir == 1 else -self.offset_x)
        base_top_y = tr.y + dest_h / 2 - slice_h_dest / 2

        for i in range(slices_to_draw):
            src_bottom = src_h - (i + 1) * slice_h_src
            dest_y = base_top_y - i * slice_h_dest
            self.attack_image.clip_composite_draw(
                0,
                src_bottom,
                src_w,
                slice_h_src,
                0,
                flip,
                base_x,
                dest_y,
                dest_w,
                slice_h_dest,
            )

    def check_attack_collision(self):
        tr = self.owner.get(TransformComponent)
        if not tr:
            return

        attack_box_x = tr.x + (self.offset_x if self.attack_dir == 1 else -self.offset_x)
        attack_box_y = tr.y + self.offset_y
        half_w = self.width * 0.5
        half_h = self.height * 0.5
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
