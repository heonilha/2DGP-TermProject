import os

from pico2d import load_image

from components.component_base import Component
from components.component_transform import TransformComponent


class HUDComponent(Component):
    _hp_bar_image = None
    _bar_base_image = None

    def __init__(self, hp_width=50, hp_height=5, mp_width=50, mp_height=5, hp_offset=40, mp_offset=50):
        super().__init__()
        self.hp_width = hp_width
        self.hp_height = hp_height
        self.mp_width = mp_width
        self.mp_height = mp_height
        self.hp_offset = hp_offset
        self.mp_offset = mp_offset

        if HUDComponent._hp_bar_image is None or HUDComponent._bar_base_image is None:
            base_dir = os.path.dirname(os.path.dirname(__file__))
            gui_dir = os.path.join(base_dir, "resource", "Image", "GUI")
            HUDComponent._hp_bar_image = load_image(os.path.join(gui_dir, "hp_bar.png"))
            HUDComponent._bar_base_image = load_image(os.path.join(gui_dir, "bar_base.png"))

    def draw(self):
        owner = self.owner
        tr = owner.get(TransformComponent)
        if not tr:
            return

        # 플레이어(Zag)는 UI에서 따로 표시하므로 HUD에서는 표시하지 않는다.
        try:
            from zag import Zag

            if isinstance(owner, Zag):
                return
        except ImportError:
            pass

        if not hasattr(owner, "combat") or owner.combat is None:
            return

        if getattr(owner, "hp", 0) <= 0:
            return

        max_hp = owner.combat.max_hp
        if max_hp <= 0:
            return

        hp_ratio = max(0.0, min(1.0, owner.hp / max_hp))

        bar_x = tr.x
        bar_y = tr.y + self.hp_offset

        HUDComponent._bar_base_image.draw(bar_x, bar_y, self.hp_width, self.hp_height)

        current_hp_width = int(self.hp_width * hp_ratio)
        if current_hp_width > 0:
            hp_fill_center_x = bar_x - self.hp_width / 2 + current_hp_width / 2
            HUDComponent._hp_bar_image.clip_draw(
                0,
                0,
                int(HUDComponent._hp_bar_image.w * hp_ratio),
                HUDComponent._hp_bar_image.h,
                hp_fill_center_x,
                bar_y,
                current_hp_width,
                self.hp_height,
            )
