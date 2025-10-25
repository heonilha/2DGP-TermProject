from pico2d import *

open_canvas()
character = load_image('ZAG_ani.png')
frame = 0
x=0
while True:
    clear_canvas()
    character.clip_draw(frame * 32, 0, 32, 64, x, 300)  # 프레임 너비 32, 높이 64
    update_canvas()
    frame = (frame + 1) % 2
    x += 5
    delay(0.1)