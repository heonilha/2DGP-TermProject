from pico2d import *
import os
from zag import Zag
BASE_DIR = os.path.dirname(__file__)

class GameUI:
    def __init__(self):
        self.hp_potion_image = load_image(os.path.join(BASE_DIR, 'resource', 'Image', 'GUI','Item', 'hp_potion.png'))
        self.mp_potion_image = load_image(os.path.join(BASE_DIR, 'resource', 'Image', 'GUI','Item', 'mp_potion.png'))
        self.gold_image = load_image(os.path.join(BASE_DIR, 'resource', 'Image', 'GUI','Item', 'bar_coin.png'))
        self.font = load_font('ENCR10B.TTF', 30)

    def draw(self, player):
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