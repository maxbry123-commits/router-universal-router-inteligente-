class AgenticLoopController:
    def __init__(self, max_rounds: int = 5, max_tools_per_round: int = 3):
        self.max_rounds = max_rounds
        self.max_tools_per_round = max_tools_per_round
        self.current_round = 0
        self.seen_calls = set()

    def can_continue(self) -> bool:
        return self.current_round < self.max_rounds

    def register_round(self):
        self.current_round += 1

    def is_repeated_call(self, tool_name: str, args: str) -> bool:
        call_signature = f'{tool_name}:{args}'
        if call_signature in self.seen_calls:
            return True
        self.seen_calls.add(call_signature)
        return False
