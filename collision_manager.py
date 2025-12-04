from enum import IntFlag

from components.component_collision import CollisionComponent


class CollisionGroup(IntFlag):
    PLAYER = 1
    MONSTER = 2
    PROJECTILE = 4


class CollisionManager:
    def __init__(self):
        self.components = []

    def register(self, obj):
        getter = getattr(obj, "get", None)
        if not callable(getter):
            return

        component = getter(CollisionComponent)
        if component and component not in self.components:
            self.components.append(component)

    def unregister(self, obj):
        getter = getattr(obj, "get", None)
        if not callable(getter):
            return

        component = getter(CollisionComponent)
        if component and component in self.components:
            self.components.remove(component)

    def clear(self):
        self.components.clear()

    def handle_collisions(self):
        for i, comp_a in enumerate(self.components):
            owner_a = comp_a.owner
            if not owner_a:
                continue
            for comp_b in self.components[i + 1 :]:
                owner_b = comp_b.owner
                if not owner_b:
                    continue

                if not (comp_a.mask & comp_b.group and comp_b.mask & comp_a.group):
                    continue

                if self._collide(comp_a, comp_b):
                    if hasattr(owner_a, "handle_collision"):
                        owner_a.handle_collision(owner_b)
                    if hasattr(owner_b, "handle_collision"):
                        owner_b.handle_collision(owner_a)

    @staticmethod
    def _collide(a, b):
        left_a, bottom_a, right_a, top_a = a.get_bb()
        left_b, bottom_b, right_b, top_b = b.get_bb()

        if left_a > right_b:
            return False
        if right_a < left_b:
            return False
        if top_a < bottom_b:
            return False
        if bottom_a > top_b:
            return False
        return True


collision_manager = CollisionManager()
