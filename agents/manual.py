from .base import BaseAgent
class ManualCLIAgent(BaseAgent):

    def choose_action(self):
        print("Current Board")
        self.environment.print_board()
        print("Available Actions")
        valid = self.environment.valid_actions
        print(valid)
        action = int(input("Choose Action: "))
        while action not in valid:
            print (f"Invalid Action: {action} - please select a valid action")
            print(valid)
            action = int(input("Choose Action: "))
        return action
