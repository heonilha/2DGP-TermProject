import os
from pico2d import clear_canvas, get_canvas_height, get_canvas_width, get_events, load_font, load_image, update_canvas
from sdl2 import SDL_BUTTON_LEFT, SDL_KEYDOWN, SDL_MOUSEBUTTONDOWN, SDL_QUIT, SDLK_ESCAPE

import game_framework
import game_world
from modes import play_mode
from zag import Zag

BASE_DIR = os.path.dirname(os.path.dirname(__file__))


class ShopMode:
    def __init__(self):
        self.player = None
        self.background = None
        self.font = None
        self.coin_image = None
        self.hp_image = None
        self.mp_image = None
        self.shop_items = []

    def init(self):
        self.player = self._get_or_create_player()
        background_path = os.path.join(BASE_DIR, "resource", "Image", "GUI", "clearEmptyImage.png")
        self.background = load_image(background_path)
        self.font = load_font("ENCR10B.TTF", 30)

        item_dir = os.path.join(BASE_DIR, "resource", "Image", "GUI", "Item")
        self.coin_image = load_image(os.path.join(item_dir, "bar_coin.png"))
        self.hp_image = load_image(os.path.join(item_dir, "hp_potion.png"))
        self.mp_image = load_image(os.path.join(item_dir, "mp_potion.png"))

        self.shop_items = [
            {
                "name": "HP Potion",
                "image": self.hp_image,
                "pos": (get_canvas_width() * 0.35, get_canvas_height() * 0.45),
                "cost": 30,
                "attr": "hp_potions",
            },
            {
                "name": "MP Potion",
                "image": self.mp_image,
                "pos": (get_canvas_width() * 0.65, get_canvas_height() * 0.45),
                "cost": 30,
                "attr": "mp_potions",
            },
        ]

    def _get_or_create_player(self):
        if game_world.player:
            return game_world.player[0]

        if getattr(play_mode, "zag", None) is not None:
            return play_mode.zag

        play_mode.zag = Zag()
        return play_mode.zag

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
        for item in self.shop_items:
            if self._point_in_item(event.x, mouse_y, item):
                self._buy_item(item)

    def _point_in_item(self, x, y, item):
        image = item["image"]
        center_x, center_y = item["pos"]
        half_w, half_h = image.w / 2, image.h / 2
        padding = 20
        return (
            center_x - half_w - padding
            <= x
            <= center_x + half_w + padding
        ) and (
            center_y - half_h - padding
            <= y
            <= center_y + half_h + padding
        )

    def _buy_item(self, item):
        cost = item["cost"]
        attr = item["attr"]
        if self.player.gold >= cost:
            self.player.gold -= cost
            setattr(self.player, attr, getattr(self.player, attr) + 1)

    def update(self):
        pass

    def draw(self):
        clear_canvas()
        center_x, center_y = get_canvas_width() / 2, get_canvas_height() / 2
        self.background.draw(center_x, center_y, get_canvas_width() * 2, get_canvas_height() * 2)

        coin_x = center_x - 100
        coin_y = center_y + 200
        self.coin_image.draw(coin_x, coin_y)
        self.font.draw(coin_x + 60, coin_y - 10, f"x {self.player.gold}", (255, 215, 0))

        for item in self.shop_items:
            image = item["image"]
            pos_x, pos_y = item["pos"]
            image.draw(pos_x, pos_y)
            self.font.draw(pos_x - 60, pos_y - image.h, f"{item['name']}", (255, 255, 255))
            self.font.draw(
                pos_x - 40,
                pos_y - image.h - 40,
                f"Price: {item['cost']}G",
                (255, 215, 0),
            )
            owned = getattr(self.player, item["attr"])
            self.font.draw(pos_x - 30, pos_y - image.h - 80, f"Owned: {owned}", (173, 216, 230))
        update_canvas()

    def pause(self):
        pass

    def resume(self):
        pass

    def finish(self):
        self.background = None
        self.font = None
        self.player = None
