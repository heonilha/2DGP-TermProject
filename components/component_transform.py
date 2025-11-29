from components.component_base import Component

class TransformComponent(Component):
    def __init__(self, x=0, y=0, w=0, h=0):
        super().__init__()
        self.x, self.y = x, y
        self.w, self.h = w, h
