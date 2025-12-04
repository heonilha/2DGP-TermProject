from components.component_base import Component


class PerceptionComponent(Component):
    def __init__(self, owner=None):
        super().__init__()
        if owner is not None:
            self.owner = owner
        self.target = None

    def distance_sq_to_target(self):
        if not self.target or not getattr(self.target, "transform", None):
            return 999_999_999
        if not getattr(self.owner, "transform", None):
            return 999_999_999

        dx = self.owner.transform.x - self.target.transform.x
        dy = self.owner.transform.y - self.target.transform.y
        return dx * dx + dy * dy

    def is_in_range(self, range_):
        return self.distance_sq_to_target() <= range_ * range_
