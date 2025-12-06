import game_framework

from ui_icon import BaseIcon


class StageIcon(BaseIcon):
    def __init__(self, x, y, image_path, target_mode, stage_id=None):
        self.target_mode = target_mode
        self.stage_id = stage_id

        def on_click():
            if self.stage_id is not None and hasattr(self.target_mode, "prepare_stage"):
                self.target_mode.prepare_stage(self.stage_id)
            game_framework.change_mode(self.target_mode)

        super().__init__(x, y, image_path, on_click)


# Example usage for arranging icons inside a mode:
# from pico2d import get_events
# from ui_icon import ShopIcon
#
# icons = [
#     StageIcon(300, 500, "stage1_icon.png", StageMode(), stage_id=1),
#     StageIcon(500, 500, "stage2_icon.png", StageMode(), stage_id=2),
#     ShopIcon(400, 300, "shop_icon.png")
# ]
#
# def handle_events():
#     for event in get_events():
#         for icon in icons:
#             icon.handle_event(event)
#
# def update():
#     for icon in icons:
#         icon.update()
#
# def draw():
#     for icon in icons:
#         icon.draw()
