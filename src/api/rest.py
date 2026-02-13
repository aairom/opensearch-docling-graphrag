"""
FastAPI REST API implementation.
"""
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Dict, Any
import base64
import os
from pathlib import Path
from datetime import datetime
import asyncio
import json
from loguru import logger

from src.api.models import (
    DocumentUploadRequest,
    DocumentProcessResponse,
    SearchRequest,
    SearchResponse,
    RAGRequest,
    RAGResponse,
    GraphStatsResponse,
    EntityConnectionsRequest,
    EntityConnectionsResponse,
    BatchProcessRequest,
    BatchProcessResponse,
    JobStatusResponse,
    HealthResponse,
    ErrorResponse,
    ProcessingStatus,
    SystemConfigResponse,
    GPUConfig
)
from src.processors import DoclingProcessor
from src.rag import OpenSearchClient, OllamaClient
from src.graphrag import Neo4jClient, GraphBuilder, GraphVisualizer
from config.settings import settings


# Initialize FastAPI app
app = FastAPI(
    title="OpenSearch-Docling-GraphRAG API",
    description="REST API for document processing, search, and knowledge graph operations",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global clients (initialized on startup)
processor: DoclingProcessor = None
opensearch_client: OpenSearchClient = None
ollama_client: OllamaClient = None
neo4j_client: Neo4jClient = None
graph_builder: GraphBuilder = None
graph_visualizer: GraphVisualizer = None

# Job tracking
active_jobs: Dict[str, Dict[str, Any]] = {}

# WebSocket connections
active_connections: List[WebSocket] = []


@app.on_event("startup")
async def startup_event():
    """Initialize clients on startup."""
    global processor, opensearch_client, ollama_client, neo4j_client, graph_builder, graph_visualizer
    
    try:
        logger.info("Initializing API clients...")
        processor = DoclingProcessor()
        opensearch_client = OpenSearchClient()
        ollama_client = OllamaClient()
        neo4j_client = Neo4jClient()
        graph_builder = GraphBuilder(neo4j_client)
        graph_visualizer = GraphVisualizer(neo4j_client)
        logger.info("API clients initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize clients: {str(e)}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    global neo4j_client
    if neo4j_client:
        neo4j_client.close()
    logger.info("API shutdown complete")


# Health and Status Endpoints

@app.get("/api/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Check system health and service availability."""
    services = {
        "opensearch": False,
        "neo4j": False,
        "ollama": False
    }
    
    try:
        # Check OpenSearch
        opensearch_client.client.cluster.health()
        services["opensearch"] = True
    except:
        pass
    
    try:
        # Check Neo4j
        neo4j_client.verify_connectivity()
        services["neo4j"] = True
    except:
        pass
    
    try:
        # Check Ollama
        ollama_client.client.list()
        services["ollama"] = True
    except:
        pass
    
    status = "healthy" if all(services.values()) else "degraded"
    
    return HealthResponse(
        status=status,
        version="1.0.0",
        services=services,
        timestamp=datetime.utcnow()
    )


@app.get("/api/config", response_model=SystemConfigResponse, tags=["System"])
async def get_config():
    """Get current system configuration."""
    gpu_available = False
    try:
        import torch
        gpu_available = torch.cuda.is_available()
    except:
        pass
    
    return SystemConfigResponse(
        ollama_model=settings.ollama_model,
        embedding_model=settings.ollama_embedding_model,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        gpu_enabled=getattr(settings, 'gpu_enabled', False),
        gpu_available=gpu_available
    )


# Document Processing Endpoints

@app.post("/api/documents/upload", response_model=DocumentProcessResponse, tags=["Documents"])
async def upload_document(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """Upload and process a single document."""
    try:
        # Save uploaded file
        file_path = Path(settings.input_dir) / file.filename
        with open(file_path, 'wb') as f:
            content = await file.read()
            f.write(content)
        
        # Process document
        doc_data = processor.process_document(str(file_path))
        
        # Generate embeddings
        texts = [chunk['text'] for chunk in doc_data['chunks']]
        embeddings = ollama_client.generate_embeddings_batch(texts)
        
        # Index in OpenSearch
        document_id = f"{Path(file.filename).stem}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        opensearch_client.index_document(
            document_id=document_id,
            file_name=file.filename,
            file_path=str(file_path),
            chunks=doc_data['chunks'],
            embeddings=embeddings,
            metadata=doc_data['metadata']
        )
        
        # Build knowledge graph
        graph_builder.build_document_graph(
            document_id=document_id,
            file_name=file.filename,
            file_path=str(file_path),
            chunks=doc_data['chunks'],
            metadata=doc_data['metadata']
        )
        
        # Broadcast to WebSocket clients
        await broadcast_message({
            "type": "document_processed",
            "document_id": document_id,
            "file_name": file.filename
        })
        
        return DocumentProcessResponse(
            document_id=document_id,
            status=ProcessingStatus.COMPLETED,
            message="Document processed successfully",
            metadata=doc_data['metadata'],
            chunks_count=len(doc_data['chunks']),
            entities_count=len(doc_data.get('entities', []))
        )
        
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/documents/batch", response_model=BatchProcessResponse, tags=["Documents"])
async def batch_process(request: BatchProcessRequest, background_tasks: BackgroundTasks):
    """Process multiple documents in batch."""
    job_id = f"batch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    
    active_jobs[job_id] = {
        "status": ProcessingStatus.PENDING,
        "total_files": len(request.file_names),
        "completed_files": 0,
        "errors": []
    }
    
    # Start background processing
    background_tasks.add_task(process_batch_job, job_id, request.file_names)
    
    return BatchProcessResponse(
        job_id=job_id,
        status=ProcessingStatus.PENDING,
        total_files=len(request.file_names),
        message="Batch processing started"
    )


@app.get("/api/documents/batch/{job_id}", response_model=JobStatusResponse, tags=["Documents"])
async def get_job_status(job_id: str):
    """Get status of a batch processing job."""
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = active_jobs[job_id]
    progress = (job["completed_files"] / job["total_files"]) * 100 if job["total_files"] > 0 else 0
    
    return JobStatusResponse(
        job_id=job_id,
        status=job["status"],
        progress=progress,
        completed_files=job["completed_files"],
        total_files=job["total_files"],
        current_file=job.get("current_file"),
        errors=job.get("errors")
    )


# Search Endpoints

@app.post("/api/search", response_model=SearchResponse, tags=["Search"])
async def search_documents(request: SearchRequest):
    """Search documents using vector similarity."""
    try:
        start_time = datetime.utcnow()
        
        # Generate query embedding
        query_embedding = ollama_client.generate_embedding(request.query)
        
        # Search in OpenSearch
        results = opensearch_client.search(query_embedding, k=request.top_k)
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        return SearchResponse(
            query=request.query,
            results=results,
            total_results=len(results),
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/rag/query", response_model=RAGResponse, tags=["RAG"])
async def rag_query(request: RAGRequest):
    """Answer questions using RAG."""
    try:
        start_time = datetime.utcnow()
        
        # Generate query embedding
        query_embedding = ollama_client.generate_embedding(request.question)
        
        # Search for relevant context
        search_results = opensearch_client.search(query_embedding, k=request.top_k)
        
        # Build context
        context = "\n\n".join([result.text for result in search_results])
        
        # Generate answer
        model = request.model or settings.ollama_model
        answer = ollama_client.generate_response(
            prompt=request.question,
            context=context,
            model=model
        )
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        return RAGResponse(
            question=request.question,
            answer=answer,
            sources=search_results,
            model_used=model,
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"RAG query error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Knowledge Graph Endpoints

@app.get("/api/graph/stats", response_model=GraphStatsResponse, tags=["Graph"])
async def get_graph_stats():
    """Get knowledge graph statistics."""
    try:
        stats = graph_visualizer.get_graph_stats()
        return GraphStatsResponse(**stats)
    except Exception as e:
        logger.error(f"Error getting graph stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/graph/connections", response_model=EntityConnectionsResponse, tags=["Graph"])
async def get_entity_connections(request: EntityConnectionsRequest):
    """Find connections for an entity."""
    try:
        connections = graph_visualizer.find_entity_connections(
            entity_name=request.entity_name,
            max_depth=request.max_depth
        )
        
        return EntityConnectionsResponse(
            entity_name=request.entity_name,
            connections=connections,
            total_connections=len(connections)
        )
    except Exception as e:
        logger.error(f"Error finding connections: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket Endpoint

@app.websocket("/api/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            # Echo back for ping/pong
            await websocket.send_text(json.dumps({"type": "pong", "timestamp": datetime.utcnow().isoformat()}))
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        logger.info("WebSocket client disconnected")


# Helper Functions

async def process_batch_job(job_id: str, file_names: List[str]):
    """Process batch job in background."""
    active_jobs[job_id]["status"] = ProcessingStatus.PROCESSING
    
    for i, file_name in enumerate(file_names):
        try:
            active_jobs[job_id]["current_file"] = file_name
            
            file_path = Path(settings.input_dir) / file_name
            if not file_path.exists():
                active_jobs[job_id]["errors"].append(f"File not found: {file_name}")
                continue
            
            # Process document (similar to upload_document)
            doc_data = processor.process_document(str(file_path))
            texts = [chunk['text'] for chunk in doc_data['chunks']]
            embeddings = ollama_client.generate_embeddings_batch(texts)
            
            document_id = f"{Path(file_name).stem}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            opensearch_client.index_document(
                document_id=document_id,
                file_name=file_name,
                file_path=str(file_path),
                chunks=doc_data['chunks'],
                embeddings=embeddings,
                metadata=doc_data['metadata']
            )
            
            graph_builder.build_document_graph(
                document_id=document_id,
                file_name=file_name,
                file_path=str(file_path),
                chunks=doc_data['chunks'],
                metadata=doc_data['metadata']
            )
            
            active_jobs[job_id]["completed_files"] += 1
            
            # Broadcast progress
            await broadcast_message({
                "type": "batch_progress",
                "job_id": job_id,
                "progress": (active_jobs[job_id]["completed_files"] / len(file_names)) * 100,
                "current_file": file_name
            })
            
        except Exception as e:
            logger.error(f"Error processing {file_name}: {str(e)}")
            active_jobs[job_id]["errors"].append(f"{file_name}: {str(e)}")
    
    active_jobs[job_id]["status"] = ProcessingStatus.COMPLETED
    active_jobs[job_id]["current_file"] = None
    
    await broadcast_message({
        "type": "batch_completed",
        "job_id": job_id
    })


async def broadcast_message(message: Dict[str, Any]):
    """Broadcast message to all WebSocket clients."""
    disconnected = []
    for connection in active_connections:
        try:
            await connection.send_text(json.dumps(message))
        except:
            disconnected.append(connection)
    
    # Remove disconnected clients
    for connection in disconnected:
        active_connections.remove(connection)


# Error Handlers

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            timestamp=datetime.utcnow()
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc),
            timestamp=datetime.utcnow()
        ).dict()
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.app_host, port=8000)

# Made with Bob
