import os
from pico2d import load_music

from common import resource_path

_current_music = None
_music_cache = {}


def _get_music(track_name: str):
    global _music_cache
    if track_name not in _music_cache:
        music_path = resource_path(f"bgm/{track_name}.mp3")
        if not os.path.exists(music_path):
            raise FileNotFoundError(f"BGM file not found: `{music_path}`")
        _music_cache[track_name] = load_music(music_path)
    return _music_cache[track_name]


def _play(track_name: str):
    global _current_music
    music = _get_music(track_name)
    if _current_music is not None and _current_music is not music:
        _current_music.stop()
    _current_music = music
    music.repeat_play()


def stop_bgm():
    global _current_music
    if _current_music is not None:
        _current_music.stop()
        _current_music = None


def play_title_bgm():
    _play("title")


def play_select_bgm():
    _play("select")


def play_stage_bgm(stage_id: int):
    _play(f"stage{stage_id}")
