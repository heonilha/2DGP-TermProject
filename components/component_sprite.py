from components.component_base import Component
from components.component_transform import TransformComponent
class SpriteComponent(Component):
    def __init__(self, image, frame_w, frame_h):
        super().__init__()
        self.image = image
        self.frame_w = frame_w
        self.frame_h = frame_h
        self.frame = 0
        self.flip = ''  # '' or 'h'

    def draw(self):
        tr = self.owner.get(TransformComponent)
        if not tr:
            return

        self.image.clip_composite_draw(
            int(self.frame) * self.frame_w, 0,
            self.frame_w, self.frame_h,
            0, self.flip,
            tr.x, tr.y,
            tr.w, tr.h
        )
