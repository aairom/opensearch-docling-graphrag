# Architecture Documentation

## System Overview

The OpenSearch-Docling-GraphRAG system is a comprehensive document processing and retrieval-augmented generation platform that combines multiple technologies to provide advanced document understanding and question-answering capabilities.

## High-Level Architecture

```mermaid
graph TB
    subgraph "Presentation Layer"
        UI[Streamlit Web UI]
    end
    
    subgraph "Application Layer"
        APP[Python Application]
        DP[Document Processor]
        RAG[RAG Engine]
        GR[Graph Builder]
    end
    
    subgraph "Data Layer"
        OS[(OpenSearch<br/>Vector Store)]
        NEO[(Neo4j<br/>Graph DB)]
        FS[File System<br/>Input/Output]
    end
    
    subgraph "AI/ML Layer"
        OLLAMA[Ollama<br/>LLM Service]
        EMB[Embedding Models]
        GEN[Generation Models]
    end
    
    UI --> APP
    APP --> DP
    APP --> RAG
    APP --> GR
    
    DP --> OS
    DP --> NEO
    DP --> FS
    
    RAG --> OS
    RAG --> OLLAMA
    
    GR --> NEO
    
    OLLAMA --> EMB
    OLLAMA --> GEN
    
    style UI fill:#e1f5ff
    style APP fill:#fff3e0
    style OS fill:#f3e5f5
    style NEO fill:#e8f5e9
    style OLLAMA fill:#fce4ec
```

## Component Architecture

### 1. Document Processing Pipeline

```mermaid
flowchart LR
    A[Input Document] --> B[Docling Parser]
    B --> C[Text Extraction]
    C --> D[Chunking]
    D --> E[Metadata Extraction]
    E --> F[Entity Recognition]
    F --> G{Storage}
    G --> H[OpenSearch]
    G --> I[Neo4j]
    G --> J[File System]
    
    style A fill:#fff3e0
    style B fill:#e1f5ff
    style G fill:#f3e5f5
    style H fill:#e8f5e9
    style I fill:#e8f5e9
    style J fill:#fff9c4
```

### 2. RAG Query Flow

```mermaid
sequenceDiagram
    participant User
    participant UI
    participant RAG
    participant Ollama
    participant OpenSearch
    
    User->>UI: Submit Query
    UI->>RAG: Process Query
    RAG->>Ollama: Generate Query Embedding
    Ollama-->>RAG: Embedding Vector
    RAG->>OpenSearch: Vector Search
    OpenSearch-->>RAG: Top-K Documents
    RAG->>Ollama: Generate Response with Context
    Ollama-->>RAG: Generated Answer
    RAG-->>UI: Answer + Sources
    UI-->>User: Display Results
```

### 3. Knowledge Graph Construction

```mermaid
flowchart TD
    A[Document Chunks] --> B[Entity Extraction]
    B --> C{Entity Types}
    C --> D[Person]
    C --> E[Organization]
    C --> F[Location]
    C --> G[Date]
    C --> H[Other]
    
    D --> I[Create Nodes]
    E --> I
    F --> I
    G --> I
    H --> I
    
    I --> J[Link to Chunks]
    J --> K[Create Relationships]
    K --> L[Neo4j Graph]
    
    style A fill:#fff3e0
    style C fill:#e1f5ff
    style L fill:#e8f5e9
```

## Data Flow

### Document Ingestion

```mermaid
flowchart TB
    Start([Start]) --> Upload[Upload/Select Document]
    Upload --> Parse[Parse with Docling]
    Parse --> Extract[Extract Text & Metadata]
    Extract --> Chunk[Create Text Chunks]
    Chunk --> Embed[Generate Embeddings]
    Embed --> Index[Index in OpenSearch]
    Index --> Graph[Build Knowledge Graph]
    Graph --> Save[Save to Output]
    Save --> End([End])
    
    style Start fill:#e8f5e9
    style End fill:#e8f5e9
    style Parse fill:#e1f5ff
    style Embed fill:#fce4ec
    style Index fill:#f3e5f5
    style Graph fill:#e8f5e9
```

### Query Processing

```mermaid
flowchart TB
    Start([User Query]) --> Embed[Generate Query Embedding]
    Embed --> Search[Vector Search in OpenSearch]
    Search --> Retrieve[Retrieve Top-K Chunks]
    Retrieve --> Context[Build Context]
    Context --> Generate[Generate Answer with LLM]
    Generate --> Format[Format Response]
    Format --> Display[Display to User]
    Display --> End([End])
    
    style Start fill:#e8f5e9
    style End fill:#e8f5e9
    style Embed fill:#fce4ec
    style Search fill:#f3e5f5
    style Generate fill:#fce4ec
```

## Technology Stack

### Core Technologies

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Document Processing | Docling | Parse and extract content from various formats |
| Vector Store | OpenSearch | Store and search document embeddings |
| Knowledge Graph | Neo4j | Store and query entity relationships |
| LLM/Embeddings | Ollama | Generate embeddings and responses |
| Web Framework | Streamlit | User interface |
| Language | Python 3.11+ | Application logic |

### Supporting Technologies

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Containerization | Docker | Application packaging |
| Orchestration | Docker Compose | Multi-service management |
| Deployment | Kubernetes | Production deployment |
| Logging | Loguru | Application logging |
| Configuration | Pydantic | Settings management |

## Deployment Architecture

### Docker Compose Deployment

```mermaid
graph TB
    subgraph "Docker Network"
        APP[App Container<br/>Port 8501]
        OS[OpenSearch<br/>Port 9200]
        NEO[Neo4j<br/>Ports 7474, 7687]
        OSD[OpenSearch Dashboards<br/>Port 5601]
    end
    
    subgraph "Host System"
        OLLAMA[Ollama Service<br/>Port 11434]
        VOL1[Volume: opensearch-data]
        VOL2[Volume: neo4j-data]
        VOL3[Volume: input/output]
    end
    
    APP --> OS
    APP --> NEO
    APP --> OLLAMA
    APP --> VOL3
    OS --> VOL1
    NEO --> VOL2
    OSD --> OS
    
    style APP fill:#e1f5ff
    style OS fill:#f3e5f5
    style NEO fill:#e8f5e9
    style OLLAMA fill:#fce4ec
```

### Kubernetes Deployment

```mermaid
graph TB
    subgraph "Kubernetes Cluster"
        subgraph "Namespace: docling-rag"
            ING[Ingress]
            
            subgraph "Application"
                APP1[App Pod 1]
                APP2[App Pod 2]
                SVC_APP[App Service<br/>LoadBalancer]
            end
            
            subgraph "OpenSearch"
                OS[OpenSearch Pod]
                SVC_OS[OpenSearch Service]
                PVC_OS[PVC: 10Gi]
            end
            
            subgraph "Neo4j"
                NEO[Neo4j Pod]
                SVC_NEO[Neo4j Service]
                PVC_NEO[PVC: 10Gi]
            end
            
            CM[ConfigMap]
            SEC[Secrets]
        end
    end
    
    ING --> SVC_APP
    SVC_APP --> APP1
    SVC_APP --> APP2
    
    APP1 --> SVC_OS
    APP2 --> SVC_OS
    APP1 --> SVC_NEO
    APP2 --> SVC_NEO
    
    SVC_OS --> OS
    SVC_NEO --> NEO
    
    OS --> PVC_OS
    NEO --> PVC_NEO
    
    APP1 -.-> CM
    APP1 -.-> SEC
    APP2 -.-> CM
    APP2 -.-> SEC
    
    style ING fill:#fff3e0
    style APP1 fill:#e1f5ff
    style APP2 fill:#e1f5ff
    style OS fill:#f3e5f5
    style NEO fill:#e8f5e9
```

## Security Architecture

```mermaid
flowchart TB
    subgraph "Security Layers"
        A[Network Security]
        B[Authentication]
        C[Authorization]
        D[Data Encryption]
        E[Secrets Management]
    end
    
    A --> A1[Firewall Rules]
    A --> A2[Network Policies]
    
    B --> B1[OpenSearch Auth]
    B --> B2[Neo4j Auth]
    
    C --> C1[RBAC]
    C --> C2[Service Accounts]
    
    D --> D1[TLS/SSL]
    D --> D2[At-Rest Encryption]
    
    E --> E1[Kubernetes Secrets]
    E --> E2[Environment Variables]
    
    style A fill:#ffebee
    style B fill:#fff3e0
    style C fill:#e8f5e9
    style D fill:#e1f5ff
    style E fill:#f3e5f5
```

## Scalability Considerations

### Horizontal Scaling

```mermaid
graph LR
    LB[Load Balancer] --> APP1[App Instance 1]
    LB --> APP2[App Instance 2]
    LB --> APP3[App Instance 3]
    
    APP1 --> OS[OpenSearch Cluster]
    APP2 --> OS
    APP3 --> OS
    
    APP1 --> NEO[Neo4j Cluster]
    APP2 --> NEO
    APP3 --> NEO
    
    style LB fill:#fff3e0
    style APP1 fill:#e1f5ff
    style APP2 fill:#e1f5ff
    style APP3 fill:#e1f5ff
    style OS fill:#f3e5f5
    style NEO fill:#e8f5e9
```

### Performance Optimization

1. **Caching Strategy**
   - Embedding cache for frequently queried texts
   - Document metadata cache
   - Graph query result cache

2. **Batch Processing**
   - Parallel document processing
   - Bulk indexing in OpenSearch
   - Batch graph operations

3. **Resource Management**
   - Connection pooling
   - Memory-efficient chunking
   - Async operations where possible

## Monitoring & Observability

```mermaid
graph TB
    subgraph "Application"
        APP[App Logs]
        METRICS[Metrics]
    end
    
    subgraph "Infrastructure"
        OS_LOGS[OpenSearch Logs]
        NEO_LOGS[Neo4j Logs]
        K8S_LOGS[K8s Logs]
    end
    
    subgraph "Monitoring Stack"
        PROM[Prometheus]
        GRAF[Grafana]
        ELK[ELK Stack]
    end
    
    APP --> PROM
    METRICS --> PROM
    OS_LOGS --> ELK
    NEO_LOGS --> ELK
    K8S_LOGS --> ELK
    APP --> ELK
    
    PROM --> GRAF
    ELK --> GRAF
    
    style APP fill:#e1f5ff
    style PROM fill:#fff3e0
    style GRAF fill:#e8f5e9
    style ELK fill:#f3e5f5
```

## API Architecture

### REST API

The system provides a comprehensive REST API built with FastAPI:

```mermaid
graph TB
    subgraph "API Layer"
        REST[REST Endpoints]
        GQL[GraphQL Endpoint]
        WS[WebSocket Endpoint]
    end
    
    subgraph "Core Services"
        DOC[Document Processing]
        SEARCH[Search Service]
        RAG[RAG Service]
        GRAPH[Graph Service]
    end
    
    subgraph "Data Layer"
        OS[(OpenSearch)]
        NEO[(Neo4j)]
    end
    
    REST --> DOC
    REST --> SEARCH
    REST --> RAG
    REST --> GRAPH
    
    GQL --> DOC
    GQL --> SEARCH
    GQL --> RAG
    GQL --> GRAPH
    
    WS --> DOC
    WS --> SEARCH
    
    DOC --> OS
    DOC --> NEO
    SEARCH --> OS
    RAG --> OS
    GRAPH --> NEO
    
    style REST fill:#e1f5ff
    style GQL fill:#f3e5f5
    style WS fill:#fff3e0
```

### API Endpoints

**REST API (Port 8000)**
- `POST /api/documents/upload` - Upload and process documents
- `POST /api/documents/batch` - Batch process documents
- `GET /api/documents/batch/{job_id}` - Get batch job status
- `POST /api/search` - Vector search
- `POST /api/rag/query` - RAG question answering
- `GET /api/graph/stats` - Graph statistics
- `POST /api/graph/connections` - Entity connections
- `GET /api/health` - Health check
- `GET /api/config` - System configuration

**GraphQL API (Port 8000)**
- `/api/graphql` - GraphQL endpoint with queries and mutations
- Interactive GraphQL playground available

**WebSocket API (Port 8000)**
- `/api/ws` - Real-time updates for document processing

### GPU Acceleration

The system supports optional GPU acceleration for:
- Document processing with Docling
- Embedding generation
- Large batch operations

Configuration via environment variables:
```bash
GPU_ENABLED=true
GPU_DEVICE_ID=0
GPU_MEMORY_FRACTION=0.8
```

## Future Enhancements

1. **Multi-tenancy Support**
   - Isolated data per tenant
   - Resource quotas
   - Custom configurations

2. **Advanced Analytics**
   - Document similarity analysis
   - Trend detection
   - Usage analytics

3. **Enhanced Security**
   - OAuth2/OIDC integration
   - Fine-grained access control
   - Audit logging

4. **Performance Improvements**
   - Distributed processing
   - Advanced caching strategies
   - Query optimization