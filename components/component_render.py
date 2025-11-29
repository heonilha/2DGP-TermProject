from components.component_base import Component
from components.component_transform import TransformComponent


class RenderComponent(Component):
    def __init__(self, image, draw_width=None, draw_height=None):
        super().__init__()
        self.image = image
        self.draw_width = draw_width
        self.draw_height = draw_height

    def draw(self):
        tr = self.owner.get(TransformComponent)
        if not tr or not self.image:
            return

        width = self.draw_width or tr.w
        height = self.draw_height or tr.h
        self.image.draw(tr.x, tr.y, width, height)
