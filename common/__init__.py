import os
import sys


def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        # PyInstaller 실행 환경
        base_path = sys._MEIPASS
    else:
        # 개발 환경: 프로젝트 루트 기준
        base_path = os.path.dirname(os.path.abspath(__file__))
        base_path = os.path.dirname(base_path)
    return os.path.join(base_path, relative_path)
