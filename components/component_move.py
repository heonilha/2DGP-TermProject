from enum import Enum
from pico2d import clamp
import game_framework

from components.component_base import Component
from components.component_sprite import SpriteComponent
from components.component_transform import TransformComponent


class MovementType(Enum):
    DIRECTIONAL = "directional"
    LINEAR = "linear"
    PARABOLIC = "parabolic"


class MovementComponent(Component):
    def __init__(self, speed=200):
        super().__init__()
        self.xdir = 0
        self.ydir = 0
        self.speed = speed
        self.face_dir = 1  # 1 = right, -1 = left

        self.type = MovementType.DIRECTIONAL
        self._path_timer = 0.0
        self._path_duration = 0.0
        self._path_start = (0.0, 0.0)
        self._path_end = (0.0, 0.0)
        self._parabola_height = 0.0
        self._on_complete = None

    def is_path_active(self):
        return self.type in (MovementType.LINEAR, MovementType.PARABOLIC)

    def _reset_path(self):
        self._path_timer = 0.0
        self._path_duration = 0.0
        self._path_start = (0.0, 0.0)
        self._path_end = (0.0, 0.0)
        self._parabola_height = 0.0
        self._on_complete = None

    def start_linear(self, start, end, duration, on_complete=None):
        self.type = MovementType.LINEAR
        self._path_timer = 0.0
        self._path_start = start
        self._path_end = end
        self._path_duration = max(0.0001, duration)
        self._on_complete = on_complete
        tr = self.owner.get(TransformComponent)
        if tr:
            tr.x, tr.y = start
        self.xdir = 0
        self.ydir = 0

    def start_parabolic(self, start, end, height, duration, on_complete=None):
        self.type = MovementType.PARABOLIC
        self._path_timer = 0.0
        self._path_start = start
        self._path_end = end
        self._path_duration = max(0.0001, duration)
        self._parabola_height = height
        self._on_complete = on_complete
        tr = self.owner.get(TransformComponent)
        if tr:
            tr.x, tr.y = start
        self.xdir = 0
        self.ydir = 0

    def update(self):
        tr = self.owner.get(TransformComponent)
        sprite = self.owner.get(SpriteComponent)
        if not tr:
            return

        if self.type == MovementType.DIRECTIONAL:
            state_machine = getattr(self.owner, "state_machine", None)
            if state_machine and state_machine.is_attacking():
                return

            dt = game_framework.frame_time

            tr.x += self.xdir * self.speed * dt
            tr.y += self.ydir * self.speed * dt
        elif self.type == MovementType.LINEAR:
            self.update_linear(tr)
        elif self.type == MovementType.PARABOLIC:
            self.update_parabolic(tr)

    def _complete_path(self):
        self.type = MovementType.DIRECTIONAL
        if self._on_complete:
            callback = self._on_complete
            self._on_complete = None
            callback()
        self._reset_path()

    def update_linear(self, tr):
        dt = game_framework.frame_time
        self._path_timer += dt
        t = min(self._path_timer / self._path_duration, 1.0)
        tr.x = (1 - t) * self._path_start[0] + t * self._path_end[0]
        tr.y = (1 - t) * self._path_start[1] + t * self._path_end[1]

        if t >= 1.0:
            self._complete_path()

    def update_parabolic(self, tr):
        dt = game_framework.frame_time
        self._path_timer += dt
        t = min(self._path_timer / self._path_duration, 1.0)
        tr.x = (1 - t) * self._path_start[0] + t * self._path_end[0]
        base_y = (1 - t) * self._path_start[1] + t * self._path_end[1]
        tr.y = base_y + 4.0 * self._parabola_height * t * (1 - t)

        if t >= 1.0:
            self._complete_path()
