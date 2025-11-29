from pico2d import draw_rectangle

from components.component_base import Component
from components.component_transform import TransformComponent


class HUDComponent(Component):
    def __init__(self, hp_width=50, hp_height=5, mp_width=50, mp_height=5, hp_offset=40, mp_offset=50):
        super().__init__()
        self.hp_width = hp_width
        self.hp_height = hp_height
        self.mp_width = mp_width
        self.mp_height = mp_height
        self.hp_offset = hp_offset
        self.mp_offset = mp_offset

    def draw(self):
        owner = self.owner
        tr = owner.get(TransformComponent)
        if not tr:
            return

        if getattr(owner, 'hp', 0) > 0:
            hp_bar_x = tr.x - self.hp_width // 2
            hp_bar_y = tr.y + self.hp_offset
            draw_rectangle(hp_bar_x, hp_bar_y, hp_bar_x + self.hp_width, hp_bar_y + self.hp_height, 100, 100, 100)
            current_hp_width = int(self.hp_width * (owner.hp / owner.combat.max_hp))
            draw_rectangle(hp_bar_x, hp_bar_y, hp_bar_x + current_hp_width, hp_bar_y + self.hp_height, 255, 0, 0)

        if getattr(owner, 'mp', 0) > 0:
            mp_bar_x = tr.x - self.mp_width // 2
            mp_bar_y = tr.y + self.mp_offset
            draw_rectangle(mp_bar_x, mp_bar_y, mp_bar_x + self.mp_width, mp_bar_y + self.mp_height, 100, 100, 100)
            current_mp_width = int(self.mp_width * (owner.mp / 100))
            draw_rectangle(mp_bar_x, mp_bar_y, mp_bar_x + current_mp_width, mp_bar_y + self.mp_height, 0, 0, 255)
