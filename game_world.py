# game_world.py

from collision_manager import CollisionGroup, collision_manager

camera = None

world = [[] for _ in range(4)]
group_objects = {group: [] for group in CollisionGroup}

player = group_objects[CollisionGroup.PLAYER]
monsters = group_objects[CollisionGroup.MONSTER]
projectiles = group_objects[CollisionGroup.PROJECTILE]


def add_object(o, depth=0):
    world[depth].append(o)
    collision_manager.register(o)

    group = getattr(o, "collision_group", None)
    if group in group_objects:
        group_objects[group].append(o)


def add_objects(ol, depth=0):
    for o in ol:
        add_object(o, depth)


def update():
    for layer in world:
        for o in layer:
            o.update()


def render():
    cam = camera
    for layer in world:
        for o in layer:
            if hasattr(o, "draw_with_camera"):
                o.draw_with_camera(cam)
            else:
                o.draw()


def clear():
    for objs in group_objects.values():
        objs.clear()

    for layer in world:
        layer.clear()

    collision_manager.clear()


def all_objects():
    result = []
    for layer in world:
        result.extend(layer)
    return result


def handle_collisions():
    collision_manager.handle_collisions()


def remove_object(o):
    for layer in world:
        if o in layer:
            layer.remove(o)
            break

    for objs in group_objects.values():
        if o in objs:
            objs.remove(o)

    collision_manager.unregister(o)