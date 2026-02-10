"""RAG (Retrieval Augmented Generation) package."""
from .opensearch_client import OpenSearchClient
from .ollama_client import OllamaClient

__all__ = ["OpenSearchClient", "OllamaClient"]

# Made with Bob
