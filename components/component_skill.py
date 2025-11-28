from component_base import Component

class SkillComponent(Component):
    def __init__(self):
        super().__init__()
        self.skills = []

    def add_skill(self, skill):
        self.skills.append(skill)

    def use(self, index, target):
        if 0 <= index < len(self.skills):
            self.skills[index].use(self.owner, target)
