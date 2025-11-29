import game_framework
from components.component_base import Component
from components.component_sprite import SpriteComponent

class AnimationComponent(Component):
    def __init__(self, frame_count, fps):
        super().__init__()
        self.frame_count = frame_count
        self.fps = fps

    def update(self):
        dt = game_framework.frame_time
        sprite = self.owner.get(SpriteComponent)
        if not sprite:
            return

        sprite.frame = (sprite.frame + self.fps * dt) % self.frame_count
