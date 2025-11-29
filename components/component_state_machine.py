from components.component_base import Component

class StateMachineComponent(Component):
    def __init__(self, state_dict, initial_state):
        super().__init__()
        self.states = state_dict  # { "IDLE": IdleState(), ... }
        self.current_state = self.states[initial_state]
        self.current_state.enter(self.owner)

    def change_state(self, name):
        self.current_state.exit(self.owner)
        self.current_state = self.states[name]
        self.current_state.enter(self.owner)

    def update(self):
        self.current_state.update(self.owner)

    def handle_event(self, event):
        new = self.current_state.handle_event(self.owner, event)
        if new:
            self.change_state(new)
