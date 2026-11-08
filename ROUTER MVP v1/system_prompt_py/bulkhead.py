import threading

class BulkheadFullError(Exception):
    pass

class Bulkhead:
    def __init__(self, name: str, max_concurrent: int):
        self.name = name
        self.max_concurrent = max_concurrent
        self.semaphore = threading.BoundedSemaphore(max_concurrent)

    def __enter__(self):
        acquired = self.semaphore.acquire(blocking=True, timeout=30.0)
        if not acquired:
            raise BulkheadFullError(f"Bulkhead '{self.name}' lleno.")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.semaphore.release()
        return False

BULKHEADS = {
    "groq": Bulkhead("groq", max_concurrent=5),
    "nvidia": Bulkhead("nvidia", max_concurrent=5),
}

def get_bulkhead(provider: str) -> Bulkhead:
    return BULKHEADS.get(provider, Bulkhead("default", max_concurrent=10))
