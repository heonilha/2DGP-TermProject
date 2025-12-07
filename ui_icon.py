from pico2d import get_canvas_height, load_image
from sdl2 import SDL_MOUSEBUTTONDOWN, SDL_BUTTON_LEFT


class BaseIcon:
    def __init__(self, x, y, image_path, on_click=None):
        self.x, self.y = x, y
        self.image = load_image(image_path)
        self.w, self.h = self.image.w, self.image.h
        self.on_click = on_click if on_click is not None else (lambda: None)

    def get_bb(self):
        return self.x - self.w / 2, self.y - self.h / 2, self.x + self.w / 2, self.y + self.h / 2

    def handle_event(self, event):
        if event.type == SDL_MOUSEBUTTONDOWN and event.button == SDL_BUTTON_LEFT:
            mouse_y = get_canvas_height() - 1 - event.y
            left, bottom, right, top = self.get_bb()
            if left <= event.x <= right and bottom <= mouse_y <= top:
                self.on_click()

    def update(self):
        pass

    def draw(self):
        self.image.draw(self.x, self.y)


class ShopIcon(BaseIcon):
    def __init__(self, x, y, image_path):
        import game_framework
        from modes.shop_mode import ShopMode

        def on_click():
            game_framework.push_mode(ShopMode())

        super().__init__(x, y, image_path, on_click)
