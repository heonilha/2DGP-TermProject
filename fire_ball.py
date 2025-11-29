import math
import os

from pico2d import load_image

from projectile import Projectile

base_dir = os.path.dirname(__file__)
image_path = os.path.join(base_dir, 'resource', 'Image', 'Character', 'Fire', 'Fire01_1.png')


class FireBall(Projectile):
    image = None

    def __init__(self, x, y, direction):
        if FireBall.image is None:
            FireBall.image = load_image(image_path)

        damage = 5
        speed = 1000

        norm = math.hypot(direction[0], direction[1])
        dir_x, dir_y = direction if norm == 0 else (direction[0] / norm, direction[1] / norm)

        super().__init__(x, y, (dir_x, dir_y), speed, damage, 30, 30, FireBall.image)
