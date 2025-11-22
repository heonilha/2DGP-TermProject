class Entity:
    def __init__(self,x,y,w=0,h=0,layer=0):
        self.x=x
        self.y=y
        self.w=w
        self.h=h
        self.layer=layer

    def update(self,dt):
        pass

    def draw(self):
        raise NotImplementedError

    def get_bb(self):
        return (self.x - self.w/2, self.y - self.h/2, self.x + self.w/2, self.y + self.h/2)