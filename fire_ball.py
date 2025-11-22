from projectile import Projectile
import game_framework
from pico2d import *
import os

base_dir = os.path.dirname(__file__)
image_path = os.path.join(base_dir, 'resource', 'Image', 'Character', 'Fire', 'Fire01_1.png')

class FireBall(Projectile):
    image = None
    def __init__(self, x, y, direction_x,direction_y):
        if FireBall.image is None:
            FireBall.image = load_image(image_path)
        damage = 5
        speed=1000
        direction = (direction_x, direction_y)
        super().__init__(x, y, direction,speed, damage,30,30)

    def draw(self):
        self.image.draw(self.x, self.y, 30, 30)

    def on_hit(self, target):
        super().on_hit(target)