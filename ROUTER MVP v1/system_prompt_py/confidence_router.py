from mode_router_v2 import route as route_by_keywords

class ConfidenceRouter:
    def __init__(self):
        pass

    def _calculate_confidence(self, task: str, mode: str) -> float:
        keywords = {
            'programacion': ['def', 'class', 'python'],
            'frontend': ['react', 'css', 'html'],
            'forense': ['error', 'traceback', 'bug']
        }
        score = 0
        for kw in keywords.get(mode, []):
            if kw in task.lower():
                score += 0.3
        return min(1.0, score)

    def route(self, task: str) -> dict:
        base_route = route_by_keywords(task)
        confidence = self._calculate_confidence(task, base_route['mode'])
        if confidence < 0.3:
            base_route['mode'] = 'programacion'
            base_route['confidence'] = 0.3
        else:
            base_route['confidence'] = confidence
        return base_route
