from .client import EmbedderClient
try:  # opcional: YAIWES inyecta su propio cliente
    from .openai import OpenAIEmbedder, OpenAIEmbedderConfig
except ImportError:
    OpenAIEmbedder = OpenAIEmbedderConfig = None

__all__ = [
    'EmbedderClient',
    'OpenAIEmbedder',
    'OpenAIEmbedderConfig',
]
