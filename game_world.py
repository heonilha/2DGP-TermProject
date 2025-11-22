# game_world.py

world = [[] for _ in range(4)]
# 2. [추가] 충돌(Collision)용: 종류별로 모아두는 리스트
player = []  # 플레이어도 리스트로 관리 (확장성 및 통일성)
monsters = []
projectiles = []

# 3. [변경] 충돌 쌍 관리: 딕셔너리 {} 대신 리스트 [] 사용
collision_pairs = []


def add_object(o, depth=0):
    # [수정 1] 화면 그리기용 리스트에 먼저 추가해야 합니다!
    world[depth].append(o)

    # 그 다음 충돌용 리스트에 분류해서 넣습니다.
    if hasattr(o, 'type'):
        if o.type == 'player':
            player.append(o)
        elif o.type == 'monster':
            monsters.append(o)
        elif o.type == 'projectile':
            projectiles.append(o)


def add_objects(ol, depth=0):
    # [수정 2] 리스트를 통째로 world에 넣으면 분류가 안 됩니다.
    # 하나씩 add_object를 호출해서 분류 과정을 거치게 하세요.
    for o in ol:
        add_object(o, depth)


def update():
    for layer in world:
        for o in layer:
            o.update()


def render():
    for layer in world:
        for o in layer:
            o.draw()


# clear()와 all_objects()는 잘 작성하셨습니다.
def clear():
    global world
    # 충돌 리스트들도 싹 비워줘야 합니다.
    player.clear()
    monsters.clear()
    projectiles.clear()

    for layer in world:
        layer.clear()


def all_objects():
    result = []
    for layer in world:
        result.extend(layer)
    return result


def collide(a, b):
    left_a, bottom_a, right_a, top_a = a.get_bb()
    left_b, bottom_b, right_b, top_b = b.get_bb()

    if left_a > right_b: return False
    if right_a < left_b: return False
    if top_a < bottom_b: return False
    if bottom_a > top_b: return False
    return True


def add_collision_pair(group_a, group_b, group_name_debug=''):
    # 리스트의 '참조(주소)'를 저장하므로, 나중에 리스트 내용이 바뀌어도 상관없음
    collision_pairs.append((group_a, group_b, group_name_debug))


def handle_collisions():
    # 등록된 모든 충돌 쌍에 대해 검사
    for group_a, group_b, title in collision_pairs:
        for a in group_a:
            for b in group_b:
                # [수정 3] ★핵심★ 실제로 부딪혔는지 확인하는 코드가 빠져 있었습니다!
                if collide(a, b):
                    print('Collision detected between', a, 'and', b, 'in group', title)
                    # 충돌했다면 양쪽에게 알려줌
                    if hasattr(a, 'handle_collision'):
                        a.handle_collision(b, title)
                    if hasattr(b, 'handle_collision'):
                        b.handle_collision(a, title)


# [수정 4] remove_collision_object 함수는 이제 필요 없습니다. (삭제)
# 우리는 monsters, projectiles 리스트 자체를 참조하고 있으므로,
# 거기서만 지우면 collision_pairs에서도 알아서 사라진 효과가 납니다.

def remove_object(o):
    # 1. 화면 그리기용 world 리스트에서 제거
    for layer in world:
        if o in layer:
            layer.remove(o)
            # 여기서 바로 return 하면 안 됩니다! 아래쪽 코드도 실행해야 함.
            break  # 루프만 탈출

    # 2. [수정 5] 충돌용 리스트에서도 제거 (안전하게 try-except 혹은 in 체크)
    # remove는 없는 걸 지우려고 하면 에러가 나므로 확인하고 지웁니다.
    if o in monsters: monsters.remove(o)
    if o in projectiles: projectiles.remove(o)
    if o in player: player.remove(o)

    # 만약 world에도 없고 위 리스트에도 없었다면 에러 발생 (선택사항)
    # raise ValueError('Cannot delete non existing object')