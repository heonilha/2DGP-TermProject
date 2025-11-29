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

    def get_bb(self):
        from components.component_collision import CollisionComponent

        collision = self.get(CollisionComponent)
        if collision:
            return collision.get_bb()
        return 0, 0, 0, 0
