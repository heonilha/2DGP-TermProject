from common import resource_path

# 스테이지별 배경과 몬스터 스폰 정보
STAGES = {
    1: {
        "id": 1,
        "background": "bg1.png",
        "monsters": [
            {"type": "SlimeKing", "count": 1},
            {"type": "Slime", "count": 5},
        ],
    },
    2: {
        "id": 2,
        "background": "bg2.png",
        "monsters": [
            {"type": "Goblin", "count": 3},
            {"type": "GoblinArcher", "count": 2},
            {"type": "GoblinKing", "count": 1},
        ],
    },
}


def get_background_path(filename: str) -> str:
    return resource_path(f"resource/Image/GUI/Stage/BackGround/{filename}")
