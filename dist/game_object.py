from components.component_transform import TransformComponent


class GameObject:
    def __init__(self):
        self.components = []
        self.active = True

    def add_component(self, comp):
        comp.owner = self
        self.components.append(comp)
        return comp

    def get(self, comp_type):
        # 원하는 컴포넌트 타입을 가져오기
        for c in self.components:
            if isinstance(c, comp_type):
                return c
        return None

    def update(self):
        for c in self.components:
            c.update()

    def draw(self):
        for c in self.components:
            c.draw()

    def draw_with_camera(self, camera):
        tr = self.get(TransformComponent)
        original_pos = None

        if tr and camera:
            original_pos = (tr.x, tr.y)
            tr.x -= camera.x
            tr.y -= camera.y

        try:
            for c in self.components:
                if hasattr(c, "draw_with_camera"):
                    c.draw_with_camera(camera)
                else:
                    c.draw()
        finally:
            if original_pos:
                tr.x, tr.y = original_pos

    def get_bb(self):
        from components.component_collision import CollisionComponent

        collision = self.get(CollisionComponent)
        if collision:
            return collision.get_bb()
        return 0, 0, 0, 0
