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

        hitbox_w = 48
        hitbox_h = 48

        super().__init__(x, y, direction, speed, damage, hitbox_w, hitbox_h, FireBall.image)
