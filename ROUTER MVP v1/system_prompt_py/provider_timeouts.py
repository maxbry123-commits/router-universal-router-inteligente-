PROVIDER_TIMEOUTS = {
    'nvidia': 120,
    'groq': 60,
    'qwen': 300
}

def get_timeout(provider: str) -> int:
    return PROVIDER_TIMEOUTS.get(provider, 120)
