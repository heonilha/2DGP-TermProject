from pico2d import *
import os
from zag import Zag
BASE_DIR = os.path.dirname(__file__)

class GameUI:
    def __init__(self):
        self.hp_potion_image = load_image(os.path.join(BASE_DIR, 'resource', 'Image', 'GUI','Item', 'hp_potion.png'))
        self.mp_potion_image = load_image(os.path.join(BASE_DIR, 'resource', 'Image', 'GUI','Item', 'mp_potion.png'))
        self.gold_image = load_image(os.path.join(BASE_DIR, 'resource', 'Image', 'GUI','Item', 'bar_coin.png'))
        self.hp_bar_image = load_image(os.path.join(BASE_DIR, 'resource', 'Image', 'GUI', 'hp_bar.png'))
        self.mp_bar_image = load_image(os.path.join(BASE_DIR, 'resource', 'Image', 'GUI', 'mp_bar.png'))
        self.font = load_font('ENCR10B.TTF', 30)

    def draw(self, player):
        canvas_height = get_canvas_height()

        bar_left = 40
        hp_bar_y = canvas_height - 40
        mp_bar_y = hp_bar_y - 30

        if getattr(player, 'combat', None) and player.combat.max_hp > 0:
            hp_ratio = max(0.0, min(1.0, player.hp / player.combat.max_hp))
            hp_width = int(self.hp_bar_image.w * hp_ratio)
            if hp_width > 0:
                hp_x = bar_left + hp_width / 2
                self.hp_bar_image.clip_draw(0, 0, hp_width, self.hp_bar_image.h, hp_x, hp_bar_y, hp_width, self.hp_bar_image.h)

        mp_ratio = max(0.0, min(1.0, getattr(player, 'mp', 0) / 100))
        mp_width = int(self.mp_bar_image.w * mp_ratio)
        if mp_width > 0:
            mp_x = bar_left + mp_width / 2
            self.mp_bar_image.clip_draw(0, 0, mp_width, self.mp_bar_image.h, mp_x, mp_bar_y, mp_width, self.mp_bar_image.h)

        # --- HP 물약 그리기 (화면 왼쪽 아래) ---
        # 이미지 그리기 (x=50, y=100)
        self.hp_potion_image.draw(50, 100)

        # 개수 텍스트 그리기 (Zag 인벤토리에서 가져옴)
        hp_count = player.hp_potions
        self.font.draw(100, 100, f'x {hp_count}', (255, 255, 255))  # 흰색 글씨

        # --- MP 물약 그리기 (HP 물약 아래) ---
        self.mp_potion_image.draw(50, 50)

        mp_count = player.mp_potions
        self.font.draw(100, 50, f'x {mp_count}', (255, 255, 255))
        # --- 골드 그리기 (화면 오른쪽 위) ---
        self.gold_image.draw(1050, 580)
        gold_count = player.gold
        self.font.draw(1100, 580, f'x {gold_count}', (255, 255, 0))  # 노란색 글씨