import numpy as np

class BaseAgent:

    def __init__(self, name):
        self.name = name
        self.environment = None

    def choose_action(self):
        action = np.random.choice(self.environment.valid_actions)
        print(f"Choosing action {action}")
        return action
