from components.component_base import Component


class PerceptionComponent(Component):
    def __init__(self, detection_range, target_getter=None):
        super().__init__()
        self.detection_range = detection_range
        self.detection_range_sq = detection_range * detection_range
        self.target_getter = target_getter
        self.override_target = None

    def set_target(self, target):
        self.override_target = target

    def get_target(self):
        if self.override_target is not None:
            return self.override_target
        if callable(self.target_getter):
            return self.target_getter()
        return None

    def distance_sq_to_target(self):
        target = self.get_target()
        if not target:
            return None
        dx = getattr(self.owner, "x", 0) - getattr(target, "x", 0)
        dy = getattr(self.owner, "y", 0) - getattr(target, "y", 0)
        return dx * dx + dy * dy

    def is_target_in_range(self):
        distance_sq = self.distance_sq_to_target()
        if distance_sq is None:
            return False
        return distance_sq <= self.detection_range_sq
