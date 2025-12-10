from components.component_base import Component
from components.component_transform import TransformComponent


class CollisionComponent(Component):
    def __init__(self, group, mask, offset_x=0, offset_y=0, width=None, height=None):
        super().__init__()
        self.group = group
        self.mask = mask
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.override_width = width
        self.override_height = height

    def get_bb(self):
        tr = self.owner.get(TransformComponent)
        if not tr:
            return 0, 0, 0, 0

        half_w = (self.override_width or tr.w) * 0.5
        half_h = (self.override_height or tr.h) * 0.5

        cx = tr.x + self.offset_x
        cy = tr.y + self.offset_y

        return cx - half_w, cy - half_h, cx + half_w, cy + half_h
