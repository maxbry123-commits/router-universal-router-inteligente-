import random
import hashlib

class RSIController:
    def __init__(self, evaluator_fn):
        self.evaluator = evaluator_fn
    def hash(self, text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()

class SimpleTES(RSIController):
    def evolve(self, code: str, iterations: int = 3) -> str:
        best = code
        best_score = self.evaluator(best)
        for _ in range(iterations):
            candidate = best.replace("pass", "return None")
            score = self.evaluator(candidate)
            if score > best_score:
                best, best_score = candidate, score
        return best

class OpenEvolve(RSIController):
    def evolve(self, code: str, population_size: int = 3) -> str:
        population = [code] + [code.replace("pass", "return 'x'") for _ in range(population_size)]
        scored = [(self.evaluator(c), c) for c in population]
        scored.sort(reverse=True, key=lambda x: x[0])
        return scored[0][1]

RSI_ENGINES = {
    "simpletes": SimpleTES,
    "openevolve": OpenEvolve
}
