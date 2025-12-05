from components.component_base import Component
from components.component_transform import TransformComponent


class RenderComponent(Component):
    def __init__(self, image, draw_width=None, draw_height=None, clip_rect=None):
        super().__init__()
        self.image = image
        self.draw_width = draw_width
        self.draw_height = draw_height
        self.clip_rect = clip_rect  # (left, bottom, width, height)
        self.rotation = 0.0
        self.flip = ""
        self.visible = True

    def draw(self):
        tr = self.owner.get(TransformComponent)
        if not tr or not self.image or not self.visible:
            return

        width = self.draw_width or tr.w
        height = self.draw_height or tr.h

        if self.clip_rect:
            left, bottom, clip_w, clip_h = self.clip_rect
            self.image.clip_composite_draw(
                left,
                bottom,
                clip_w,
                clip_h,
                self.rotation,
                self.flip,
                tr.x,
                tr.y,
                width,
                height,
            )
        else:
            self.image.composite_draw(self.rotation, self.flip, tr.x, tr.y, width, height)
