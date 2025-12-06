import os
from pico2d import clear_canvas, get_canvas_height, get_canvas_width, get_events, load_font, load_image, update_canvas
from sdl2 import SDL_BUTTON_LEFT, SDL_KEYDOWN, SDL_MOUSEBUTTONDOWN, SDL_QUIT, SDLK_ESCAPE

import game_framework
import game_world

BASE_DIR = os.path.dirname(os.path.dirname(__file__))


class ShopMode:
    def __init__(self):
        self.player = None
        self.background = None
        self.font = None
        self.hp_button = (350, 250, 300, 60)
        self.mp_button = (350, 150, 300, 60)

    def init(self):
        self.player = game_world.player[0]
        background_path = os.path.join(BASE_DIR, "resource", "Image", "GUI", "shop_bg.png")
        self.background = load_image(background_path)
        self.font = load_font("ENCR10B.TTF", 30)

    def handle_events(self):
        for event in get_events():
            if event.type == SDL_QUIT:
                game_framework.quit()
            elif event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
                game_framework.pop_mode()
            elif event.type == SDL_MOUSEBUTTONDOWN and event.button == SDL_BUTTON_LEFT:
                self._handle_click(event)

    def _handle_click(self, event):
        mouse_y = get_canvas_height() - 1 - event.y
        if self._point_in_button(event.x, mouse_y, self.hp_button):
            self.buy_hp_potion()
        elif self._point_in_button(event.x, mouse_y, self.mp_button):
            self.buy_mp_potion()

    def _point_in_button(self, x, y, button_rect):
        left, bottom, width, height = button_rect
        return left <= x <= left + width and bottom <= y <= bottom + height

    def buy_hp_potion(self):
        if self.player.gold >= 30:
            self.player.gold -= 30
            self.player.hp_potions += 1

    def buy_mp_potion(self):
        if self.player.gold >= 30:
            self.player.gold -= 30
            self.player.mp_potions += 1

    def update(self):
        pass

    def draw(self):
        clear_canvas()
        center_x, center_y = get_canvas_width() / 2, get_canvas_height() / 2
        self.background.draw(center_x, center_y)

        gold_text = f"Gold: {self.player.gold}"
        self.font.draw(center_x - 80, center_y + 150, gold_text, (255, 215, 0))
        self.font.draw(self.hp_button[0] + 10, self.hp_button[1] + 20, "Buy HP Potion - 30G", (255, 255, 255))
        self.font.draw(self.mp_button[0] + 10, self.mp_button[1] + 20, "Buy MP Potion - 30G", (255, 255, 255))
        update_canvas()

    def pause(self):
        pass

    def resume(self):
        pass

    def finish(self):
        self.background = None
        self.font = None
        self.player = None
