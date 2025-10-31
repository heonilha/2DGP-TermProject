running = None
stack = None

#현재모드 제거 후 새 모드 추가
def change_mode(mode):
    global stack
    if (len(stack)>0):
        stack[-1].finish()
        stack.pop()
    stack.append(mode)
    mode.init()

# 현재모드 일시정지 후 새 모드 추가
def push_mode(mode):
    global stack
    if (len(stack)>0):
        stack[-1].pause()
    stack.append(mode)
    mode.init()

# 현재모드 제거 후 이전 모드 재개
def pop_mode():
    global stack
    if (len(stack)>0):
        stack[-1].finish()
        stack.pop()

    if (len(stack)>0):
        stack[-1].resume()

def quit():
    global running
    running = False

def run(start_mode):
    global running, stack
    running = True
    stack = [start_mode]
    start_mode.init()

    while running:
        stack[-1].handle_events()
        stack[-1].update()
        stack[-1].draw()

    while (len(stack)>0):
        stack[-1].finish()
        stack.pop()
