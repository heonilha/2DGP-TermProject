from entity import Entity
import game_framework
import game_world

class Projectile(Entity):
    def __init__(self, x, y, direction, speed, damage, w, h, layer=1):
        super().__init__(x, y, w, h, layer)
        self.direction = direction
        self.speed = speed
        self.damage = damage
        self.type = 'projectile'

    def handle_collision(self, other, group):
        if group == 'ball:monster':
            self.on_hit(other)

    def update(self):
        dt = game_framework.frame_time
        self.x += self.direction[0] * self.speed * dt
        self.y += self.direction[1] * self.speed * dt

    def draw(self):
        # Placeholder for drawing logic
        print(f"Drawing projectile at ({self.x}, {self.y})")

    def get_bb(self):
        return super().get_bb()

    def on_hit(self, target):
        if hasattr(target, 'take_damage'):
            target.take_damage(self.damage)
        game_world.remove_object(self)