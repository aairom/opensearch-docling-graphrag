# API Documentation

Complete API reference for OpenSearch-Docling-GraphRAG.

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [REST API](#rest-api)
- [GraphQL API](#graphql-api)
- [WebSocket API](#websocket-api)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Examples](#examples)

## Overview

The OpenSearch-Docling-GraphRAG system provides three API interfaces:

1. **REST API** - Traditional HTTP endpoints for all operations
2. **GraphQL API** - Flexible query language for complex data retrieval
3. **WebSocket API** - Real-time updates for document processing

**Base URLs:**
- REST API: `http://localhost:8000/api`
- GraphQL: `http://localhost:8000/api/graphql`
- WebSocket: `ws://localhost:8000/api/ws`

**API Documentation:**
- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`
- GraphQL Playground: `http://localhost:8000/api/graphql`

## Authentication

Currently, the API does not require authentication. For production deployments, implement:
- API keys
- OAuth2/OIDC
- JWT tokens

## REST API

### System Endpoints

#### Health Check

```http
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "opensearch": true,
    "neo4j": true,
    "ollama": true
  },
  "timestamp": "2026-02-13T08:00:00Z"
}
```

#### System Configuration

```http
GET /api/config
```

**Response:**
```json
{
  "ollama_model": "ibm/granite4:latest",
  "embedding_model": "granite-embedding:278m",
  "chunk_size": 512,
  "chunk_overlap": 50,
  "gpu_enabled": false,
  "gpu_available": true
}
```

### Document Processing Endpoints

#### Upload Document

```http
POST /api/documents/upload
Content-Type: multipart/form-data
```

**Parameters:**
- `file` (required): Document file to upload

**Response:**
```json
{
  "document_id": "report_20260213_080000",
  "status": "completed",
  "message": "Document processed successfully",
  "metadata": {
    "file_name": "report.pdf",
    "file_path": "/app/input/report.pdf",
    "pages": 10,
    "format": "pdf",
    "processed_at": "2026-02-13T08:00:00Z"
  },
  "chunks_count": 45,
  "entities_count": 23
}
```

#### Batch Process Documents

```http
POST /api/documents/batch
Content-Type: application/json
```

**Request Body:**
```json
{
  "file_names": ["doc1.pdf", "doc2.docx", "doc3.txt"],
  "options": {}
}
```

**Response:**
```json
{
  "job_id": "batch_20260213_080000",
  "status": "pending",
  "total_files": 3,
  "message": "Batch processing started"
}
```

#### Get Batch Job Status

```http
GET /api/documents/batch/{job_id}
```

**Response:**
```json
{
  "job_id": "batch_20260213_080000",
  "status": "processing",
  "progress": 66.67,
  "completed_files": 2,
  "total_files": 3,
  "current_file": "doc3.txt",
  "errors": []
}
```

### Search Endpoints

#### Vector Search

```http
POST /api/search
Content-Type: application/json
```

**Request Body:**
```json
{
  "query": "What are the main findings?",
  "top_k": 5,
  "filters": {}
}
```

**Response:**
```json
{
  "query": "What are the main findings?",
  "results": [
    {
      "document_id": "report_20260213_080000",
      "chunk_id": "chunk_0",
      "text": "The main findings indicate...",
      "score": 0.92,
      "metadata": {}
    }
  ],
  "total_results": 5,
  "processing_time": 0.234
}
```

#### RAG Query

```http
POST /api/rag/query
Content-Type: application/json
```

**Request Body:**
```json
{
  "question": "What are the main findings in the report?",
  "top_k": 5,
  "model": "ibm/granite4:latest"
}
```

**Response:**
```json
{
  "question": "What are the main findings in the report?",
  "answer": "Based on the documents, the main findings are...",
  "sources": [
    {
      "document_id": "report_20260213_080000",
      "chunk_id": "chunk_0",
      "text": "The main findings indicate...",
      "score": 0.92
    }
  ],
  "model_used": "ibm/granite4:latest",
  "processing_time": 1.456
}
```

### Knowledge Graph Endpoints

#### Graph Statistics

```http
GET /api/graph/stats
```

**Response:**
```json
{
  "total_documents": 15,
  "total_chunks": 234,
  "total_entities": 89,
  "total_relationships": 156,
  "entity_types": {
    "Person": 23,
    "Organization": 15,
    "Location": 12,
    "Date": 39
  }
}
```

#### Entity Connections

```http
POST /api/graph/connections
Content-Type: application/json
```

**Request Body:**
```json
{
  "entity_name": "John Smith",
  "max_depth": 2
}
```

**Response:**
```json
{
  "entity_name": "John Smith",
  "connections": [
    {
      "entity_name": "John Smith",
      "related_entity": "Acme Corp",
      "relationship_type": "WORKS_AT",
      "distance": 1
    }
  ],
  "total_connections": 5
}
```

## GraphQL API

### Endpoint

```
POST /api/graphql
```

### Queries

#### Health Check

```graphql
query {
  health {
    status
    opensearchAvailable
    neo4jAvailable
    ollamaAvailable
    timestamp
  }
}
```

#### Search Documents

```graphql
query SearchDocuments($input: SearchInput!) {
  search(input: $input) {
    documentId
    chunkId
    text
    score
  }
}
```

**Variables:**
```json
{
  "input": {
    "query": "What are the main findings?",
    "topK": 5
  }
}
```

#### RAG Query

```graphql
query RAGQuery($input: RAGInput!) {
  ragQuery(input: $input) {
    question
    answer
    sources {
      documentId
      text
      score
    }
    modelUsed
    processingTime
  }
}
```

**Variables:**
```json
{
  "input": {
    "question": "What are the main findings?",
    "topK": 5
  }
}
```

#### Graph Statistics

```graphql
query {
  graphStats {
    totalDocuments
    totalChunks
    totalEntities
    totalRelationships
  }
}
```

#### Entity Connections

```graphql
query EntityConnections($input: EntityConnectionInput!) {
  entityConnections(input: $input) {
    entityName
    relatedEntity
    relationshipType
    distance
  }
}
```

**Variables:**
```json
{
  "input": {
    "entityName": "John Smith",
    "maxDepth": 2
  }
}
```

#### List Entities

```graphql
query {
  entities(entityType: "Person") {
    name
    type
    documentCount
  }
}
```

### Mutations

#### Process Document

```graphql
mutation ProcessDocument($fileName: String!) {
  processDocument(fileName: $fileName) {
    documentId
    metadata {
      fileName
      pages
      format
    }
    chunksCount
    entitiesCount
  }
}
```

**Variables:**
```json
{
  "fileName": "report.pdf"
}
```

## WebSocket API

### Connection

```javascript
const ws = new WebSocket('ws://localhost:8000/api/ws');

ws.onopen = () => {
  console.log('Connected to WebSocket');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('WebSocket connection closed');
};
```

### Message Types

#### Document Processed

```json
{
  "type": "document_processed",
  "document_id": "report_20260213_080000",
  "file_name": "report.pdf"
}
```

#### Batch Progress

```json
{
  "type": "batch_progress",
  "job_id": "batch_20260213_080000",
  "progress": 66.67,
  "current_file": "doc3.txt"
}
```

#### Batch Completed

```json
{
  "type": "batch_completed",
  "job_id": "batch_20260213_080000"
}
```

#### Ping/Pong

Send:
```json
{
  "type": "ping"
}
```

Receive:
```json
{
  "type": "pong",
  "timestamp": "2026-02-13T08:00:00Z"
}
```

## Error Handling

### Error Response Format

```json
{
  "error": "Error message",
  "detail": "Detailed error information",
  "timestamp": "2026-02-13T08:00:00Z"
}
```

### HTTP Status Codes

- `200 OK` - Successful request
- `201 Created` - Resource created
- `400 Bad Request` - Invalid request parameters
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

## Rate Limiting

Currently, no rate limiting is implemented. For production:
- Implement rate limiting per IP/API key
- Use Redis for distributed rate limiting
- Configure limits based on endpoint

## Examples

### Python Example

```python
import requests

# Upload document
with open('document.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/documents/upload',
        files={'file': f}
    )
    print(response.json())

# Search
response = requests.post(
    'http://localhost:8000/api/search',
    json={
        'query': 'What are the main findings?',
        'top_k': 5
    }
)
print(response.json())

# RAG Query
response = requests.post(
    'http://localhost:8000/api/rag/query',
    json={
        'question': 'Summarize the key points',
        'top_k': 5
    }
)
print(response.json())
```

### JavaScript Example

```javascript
// Upload document
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('http://localhost:8000/api/documents/upload', {
  method: 'POST',
  body: formData
})
  .then(response => response.json())
  .then(data => console.log(data));

// Search
fetch('http://localhost:8000/api/search', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    query: 'What are the main findings?',
    top_k: 5
  })
})
  .then(response => response.json())
  .then(data => console.log(data));
```

### cURL Examples

```bash
# Health check
curl http://localhost:8000/api/health

# Upload document
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@document.pdf"

# Search
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the main findings?", "top_k": 5}'

# RAG Query
curl -X POST http://localhost:8000/api/rag/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Summarize the key points", "top_k": 5}'

# Graph stats
curl http://localhost:8000/api/graph/stats
```

## GPU Acceleration

The API supports GPU acceleration for improved performance:

```bash
# Enable GPU in environment
export GPU_ENABLED=true
export GPU_DEVICE_ID=0
export GPU_MEMORY_FRACTION=0.8
```

Check GPU status:
```http
GET /api/config
```

Response includes GPU information:
```json
{
  "gpu_enabled": true,
  "gpu_available": true
}
```

## Support

For issues or questions:
- Check the [User Guide](USER_GUIDE.md)
- Review [Architecture Documentation](ARCHITECTURE.md)
- See [Deployment Guide](DEPLOYMENT.md)