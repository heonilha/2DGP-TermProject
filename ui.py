from pico2d import *
import os
from zag import Zag
BASE_DIR = os.path.dirname(__file__)

class GameUI:
    def __init__(self):
        self.hp_potion_image = load_image(os.path.join(BASE_DIR, 'resource', 'Image', 'GUI','Item', 'hp_potion.png'))
        self.mp_potion_image = load_image(os.path.join(BASE_DIR, 'resource', 'Image', 'GUI','Item', 'mp_potion.png'))
        self.gold_image = load_image(os.path.join(BASE_DIR, 'resource', 'Image', 'GUI','Item', 'bar_coin.png'))
        gui_dir = os.path.join(BASE_DIR, 'resource', 'Image', 'GUI')
        self.hp_bar_image = load_image(os.path.join(gui_dir, 'hp_bar.png'))
        self.mp_bar_image = load_image(os.path.join(gui_dir, 'mp_bar.png'))
        self.bar_base_image = load_image(os.path.join(gui_dir, 'bar_base.png'))
        self.font = load_font('ENCR10B.TTF', 30)

    def draw(self, player):
        canvas_width, canvas_height = get_canvas_width(), get_canvas_height()
        ui_left_x = 200
        hp_bar_y = canvas_height - 80
        mp_bar_y = canvas_height - 120

        max_hp = player.combat.max_hp if hasattr(player, 'combat') and player.combat else 1
        hp_ratio = max(0.0, min(1.0, player.hp / max_hp)) if hasattr(player, 'hp') else 0.0

        max_mp = getattr(player, 'max_mp', 100)
        mp_ratio = max(0.0, min(1.0, player.mp / max_mp)) if hasattr(player, 'mp') else 0.0

        bar_width = 250
        bar_height = 28

        # HP Bar
        self.bar_base_image.draw(ui_left_x, hp_bar_y, bar_width, bar_height)
        current_hp_width = int(bar_width * hp_ratio)
        if current_hp_width > 0:
            hp_fill_center = ui_left_x - bar_width / 2 + current_hp_width / 2
            self.hp_bar_image.clip_draw(
                0,
                0,
                int(self.hp_bar_image.w * hp_ratio),
                self.hp_bar_image.h,
                hp_fill_center,
                hp_bar_y,
                current_hp_width,
                bar_height,
            )

        # MP Bar
        self.bar_base_image.draw(ui_left_x, mp_bar_y, bar_width, bar_height)
        current_mp_width = int(bar_width * mp_ratio)
        if current_mp_width > 0:
            mp_fill_center = ui_left_x - bar_width / 2 + current_mp_width / 2
            self.mp_bar_image.clip_draw(
                0,
                0,
                int(self.mp_bar_image.w * mp_ratio),
                self.mp_bar_image.h,
                mp_fill_center,
                mp_bar_y,
                current_mp_width,
                bar_height,
            )

        # --- HP 물약 그리기 (화면 왼쪽 아래) ---
        # 이미지 그리기 (x=50, y=100)
        self.hp_potion_image.draw(250, 160)

        # 개수 텍스트 그리기 (Zag 인벤토리에서 가져옴)
        hp_count = player.hp_potions
        self.font.draw(300, 160, f'x {hp_count}', (255, 255, 255))  # 흰색 글씨

        # --- MP 물약 그리기 (HP 물약 아래) ---
        self.mp_potion_image.draw(250, 100)

        mp_count = player.mp_potions
        self.font.draw(300, 100, f'x {mp_count}', (255, 255, 255))