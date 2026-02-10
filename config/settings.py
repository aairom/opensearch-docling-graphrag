"""
Configuration settings for the OpenSearch-Docling-GraphRAG application.
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Ollama Configuration
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "ibm/granite4:latest"
    ollama_embedding_model: str = "granite-embedding:278m"
    
    # OpenSearch Configuration
    opensearch_host: str = "localhost"
    opensearch_port: int = 9200
    opensearch_user: str = "admin"
    opensearch_password: str = "admin"
    opensearch_index: str = "documents"
    opensearch_use_ssl: bool = False
    opensearch_verify_certs: bool = False
    
    # Neo4j Configuration
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    
    # Application Configuration
    app_host: str = "0.0.0.0"
    app_port: int = 8501
    input_dir: str = "./input"
    output_dir: str = "./output"
    
    # Processing Configuration
    batch_size: int = 10
    chunk_size: int = 512
    chunk_overlap: int = 50
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

# Ensure directories exist
os.makedirs(settings.input_dir, exist_ok=True)
os.makedirs(settings.output_dir, exist_ok=True)

# Made with Bob
