"""
Pydantic models for API requests and responses.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ProcessingStatus(str, Enum):
    """Document processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentUploadRequest(BaseModel):
    """Request model for document upload."""
    file_name: str = Field(..., description="Name of the file")
    content_base64: Optional[str] = Field(None, description="Base64 encoded file content")


class DocumentMetadata(BaseModel):
    """Document metadata model."""
    file_name: str
    file_path: str
    file_size: Optional[int] = None
    pages: Optional[int] = None
    format: Optional[str] = None
    processed_at: datetime


class ChunkData(BaseModel):
    """Text chunk model."""
    chunk_id: str
    text: str
    page: Optional[int] = None
    position: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class DocumentProcessResponse(BaseModel):
    """Response model for document processing."""
    document_id: str
    status: ProcessingStatus
    message: str
    metadata: Optional[DocumentMetadata] = None
    chunks_count: Optional[int] = None
    entities_count: Optional[int] = None


class SearchRequest(BaseModel):
    """Request model for search queries."""
    query: str = Field(..., description="Search query text")
    top_k: int = Field(5, ge=1, le=20, description="Number of results to return")
    filters: Optional[Dict[str, Any]] = Field(None, description="Optional filters")


class SearchResult(BaseModel):
    """Individual search result."""
    document_id: str
    chunk_id: str
    text: str
    score: float
    metadata: Optional[Dict[str, Any]] = None


class SearchResponse(BaseModel):
    """Response model for search queries."""
    query: str
    results: List[SearchResult]
    total_results: int
    processing_time: float


class RAGRequest(BaseModel):
    """Request model for RAG queries."""
    question: str = Field(..., description="Question to answer")
    top_k: int = Field(5, ge=1, le=20, description="Number of context chunks")
    model: Optional[str] = Field(None, description="LLM model to use")


class RAGResponse(BaseModel):
    """Response model for RAG queries."""
    question: str
    answer: str
    sources: List[SearchResult]
    model_used: str
    processing_time: float


class EntityData(BaseModel):
    """Entity data model."""
    name: str
    type: str
    properties: Optional[Dict[str, Any]] = None


class GraphStatsResponse(BaseModel):
    """Response model for graph statistics."""
    total_documents: int
    total_chunks: int
    total_entities: int
    total_relationships: int
    entity_types: Dict[str, int]


class EntityConnectionsRequest(BaseModel):
    """Request model for entity connections."""
    entity_name: str = Field(..., description="Name of the entity")
    max_depth: int = Field(2, ge=1, le=5, description="Maximum connection depth")


class EntityConnectionsResponse(BaseModel):
    """Response model for entity connections."""
    entity_name: str
    connections: List[Dict[str, Any]]
    total_connections: int


class BatchProcessRequest(BaseModel):
    """Request model for batch processing."""
    file_names: List[str] = Field(..., description="List of files to process")
    options: Optional[Dict[str, Any]] = Field(None, description="Processing options")


class BatchProcessResponse(BaseModel):
    """Response model for batch processing."""
    job_id: str
    status: ProcessingStatus
    total_files: int
    message: str


class JobStatusResponse(BaseModel):
    """Response model for job status."""
    job_id: str
    status: ProcessingStatus
    progress: float = Field(..., ge=0.0, le=100.0)
    completed_files: int
    total_files: int
    current_file: Optional[str] = None
    errors: Optional[List[str]] = None


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    version: str
    services: Dict[str, bool]
    timestamp: datetime


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: Optional[str] = None
    timestamp: datetime


class GPUConfig(BaseModel):
    """GPU acceleration configuration."""
    enabled: bool = Field(False, description="Enable GPU acceleration")
    device_id: int = Field(0, description="GPU device ID")
    memory_fraction: float = Field(0.8, ge=0.1, le=1.0, description="GPU memory fraction")


class SystemConfigResponse(BaseModel):
    """System configuration response."""
    ollama_model: str
    embedding_model: str
    chunk_size: int
    chunk_overlap: int
    gpu_enabled: bool
    gpu_available: bool

# Made with Bob
