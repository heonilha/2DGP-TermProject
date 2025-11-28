from entity import Entity

class CombatEntity(Entity):
    def __init__(self,x,y,w,h,layer=0,hp=100):
        super().__init__(x,y,w,h,layer)
        self.hp = hp
        self.max_hp = hp


    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.on_death()

    def attack(self):
        pass

    def on_death(self):
        pass
