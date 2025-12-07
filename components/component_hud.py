import os

from pico2d import load_image

from components.component_base import Component
from components.component_transform import TransformComponent


BASE_DIR = os.path.dirname(os.path.dirname(__file__))


class HUDComponent(Component):
    hp_bar_image = None

    def __init__(self, hp_offset=40):
        super().__init__()
        self.hp_offset = hp_offset

        if HUDComponent.hp_bar_image is None:
            hp_bar_path = os.path.join(BASE_DIR, 'resource', 'Image', 'GUI', 'hp_bar.png')
            HUDComponent.hp_bar_image = load_image(hp_bar_path)

    def draw(self):
        owner = self.owner

        # 플레이어는 UI에서 HP/MP를 그리므로 HUD는 그리지 않는다.
        if getattr(owner, "use_ui_hp_bar", False):
            return

        tr = owner.get(TransformComponent)
        combat = getattr(owner, 'combat', None)
        if not tr or not combat or combat.max_hp <= 0:
            return

        if combat.hp <= 0:
            return

        hp_ratio = max(0.0, min(1.0, combat.hp / combat.max_hp))
        bar_width = int(HUDComponent.hp_bar_image.w * hp_ratio)
        bar_height = HUDComponent.hp_bar_image.h

        if bar_width > 0:
            bar_left = tr.x - HUDComponent.hp_bar_image.w // 2
            bar_x = bar_left + bar_width / 2
            bar_y = tr.y + self.hp_offset
            HUDComponent.hp_bar_image.clip_draw(0, 0, bar_width, bar_height, bar_x, bar_y, bar_width, bar_height)
