"""
GraphQL API implementation using Strawberry.
"""
import strawberry
from strawberry.fastapi import GraphQLRouter
from typing import List, Optional
from datetime import datetime
from loguru import logger

from src.processors import DoclingProcessor
from src.rag import OpenSearchClient, OllamaClient
from src.graphrag import Neo4jClient, GraphBuilder, GraphVisualizer
from config.settings import settings


# GraphQL Types

@strawberry.type
class DocumentMetadata:
    """Document metadata type."""
    file_name: str
    file_path: str
    file_size: Optional[int] = None
    pages: Optional[int] = None
    format: Optional[str] = None
    processed_at: str


@strawberry.type
class Chunk:
    """Text chunk type."""
    chunk_id: str
    text: str
    page: Optional[int] = None
    position: Optional[int] = None


@strawberry.type
class Document:
    """Document type."""
    document_id: str
    metadata: DocumentMetadata
    chunks_count: int
    entities_count: int


@strawberry.type
class SearchResult:
    """Search result type."""
    document_id: str
    chunk_id: str
    text: str
    score: float


@strawberry.type
class RAGAnswer:
    """RAG answer type."""
    question: str
    answer: str
    sources: List[SearchResult]
    model_used: str
    processing_time: float


@strawberry.type
class Entity:
    """Entity type."""
    name: str
    type: str
    document_count: int


@strawberry.type
class GraphStats:
    """Graph statistics type."""
    total_documents: int
    total_chunks: int
    total_entities: int
    total_relationships: int


@strawberry.type
class EntityConnection:
    """Entity connection type."""
    entity_name: str
    related_entity: str
    relationship_type: str
    distance: int


@strawberry.type
class SystemHealth:
    """System health type."""
    status: str
    opensearch_available: bool
    neo4j_available: bool
    ollama_available: bool
    timestamp: str


# GraphQL Inputs

@strawberry.input
class SearchInput:
    """Search input type."""
    query: str
    top_k: int = 5


@strawberry.input
class RAGInput:
    """RAG query input type."""
    question: str
    top_k: int = 5
    model: Optional[str] = None


@strawberry.input
class EntityConnectionInput:
    """Entity connection input type."""
    entity_name: str
    max_depth: int = 2


# Context class for dependency injection
class Context:
    """GraphQL context with clients."""
    def __init__(self):
        self.processor = DoclingProcessor()
        self.opensearch_client = OpenSearchClient()
        self.ollama_client = OllamaClient()
        self.neo4j_client = Neo4jClient()
        self.graph_builder = GraphBuilder(self.neo4j_client)
        self.graph_visualizer = GraphVisualizer(self.neo4j_client)


# Queries

@strawberry.type
class Query:
    """GraphQL queries."""
    
    @strawberry.field
    async def health(self) -> SystemHealth:
        """Check system health."""
        opensearch_ok = False
        neo4j_ok = False
        ollama_ok = False
        
        try:
            context = Context()
            opensearch_ok = True
            neo4j_ok = True
            ollama_ok = True
        except:
            pass
        
        status = "healthy" if all([opensearch_ok, neo4j_ok, ollama_ok]) else "degraded"
        
        return SystemHealth(
            status=status,
            opensearch_available=opensearch_ok,
            neo4j_available=neo4j_ok,
            ollama_available=ollama_ok,
            timestamp=datetime.utcnow().isoformat()
        )
    
    @strawberry.field
    async def search(self, input: SearchInput) -> List[SearchResult]:
        """Search documents."""
        try:
            context = Context()
            
            # Generate query embedding
            query_embedding = context.ollama_client.generate_embedding(input.query)
            
            # Search
            results = context.opensearch_client.search(query_embedding, k=input.top_k)
            
            return [
                SearchResult(
                    document_id=r.get('document_id', ''),
                    chunk_id=r.get('chunk_id', ''),
                    text=r.get('text', ''),
                    score=r.get('score', 0.0)
                )
                for r in results
            ]
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            raise
    
    @strawberry.field
    async def rag_query(self, input: RAGInput) -> RAGAnswer:
        """Answer question using RAG."""
        try:
            context = Context()
            start_time = datetime.utcnow()
            
            # Generate query embedding
            query_embedding = context.ollama_client.generate_embedding(input.question)
            
            # Search for context
            search_results = context.opensearch_client.search(query_embedding, k=input.top_k)
            
            # Build context
            context_text = "\n\n".join([r.get('text', '') for r in search_results])
            
            # Generate answer
            model = input.model or settings.ollama_model
            answer = context.ollama_client.generate_response(
                prompt=input.question,
                context=context_text
            )
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            sources = [
                SearchResult(
                    document_id=r.get('document_id', ''),
                    chunk_id=r.get('chunk_id', ''),
                    text=r.get('text', ''),
                    score=r.get('score', 0.0)
                )
                for r in search_results
            ]
            
            return RAGAnswer(
                question=input.question,
                answer=answer,
                sources=sources,
                model_used=model,
                processing_time=processing_time
            )
        except Exception as e:
            logger.error(f"RAG query error: {str(e)}")
            raise
    
    @strawberry.field
    async def graph_stats(self) -> GraphStats:
        """Get knowledge graph statistics."""
        try:
            context = Context()
            
            # Get stats from Neo4j
            with context.neo4j_client.driver.session() as session:
                result = session.run("""
                    MATCH (d:Document) 
                    OPTIONAL MATCH (c:Chunk)
                    OPTIONAL MATCH (e:Entity)
                    OPTIONAL MATCH ()-[r]->()
                    RETURN 
                        count(DISTINCT d) as docs,
                        count(DISTINCT c) as chunks,
                        count(DISTINCT e) as entities,
                        count(DISTINCT r) as relationships
                """)
                record = result.single()
                
                return GraphStats(
                    total_documents=record['docs'],
                    total_chunks=record['chunks'],
                    total_entities=record['entities'],
                    total_relationships=record['relationships']
                )
        except Exception as e:
            logger.error(f"Error getting graph stats: {str(e)}")
            raise
    
    @strawberry.field
    async def entity_connections(self, input: EntityConnectionInput) -> List[EntityConnection]:
        """Find entity connections."""
        try:
            context = Context()
            
            with context.neo4j_client.driver.session() as session:
                result = session.run("""
                    MATCH path = (e1:Entity {name: $entity_name})-[*1..%d]-(e2:Entity)
                    WHERE e1 <> e2
                    RETURN 
                        e1.name as entity1,
                        e2.name as entity2,
                        type(relationships(path)[0]) as rel_type,
                        length(path) as distance
                    LIMIT 50
                """ % input.max_depth, entity_name=input.entity_name)
                
                connections = []
                for record in result:
                    connections.append(EntityConnection(
                        entity_name=record['entity1'],
                        related_entity=record['entity2'],
                        relationship_type=record['rel_type'] or 'RELATED_TO',
                        distance=record['distance']
                    ))
                
                return connections
        except Exception as e:
            logger.error(f"Error finding connections: {str(e)}")
            raise
    
    @strawberry.field
    async def entities(self, entity_type: Optional[str] = None) -> List[Entity]:
        """List entities, optionally filtered by type."""
        try:
            context = Context()
            
            query = """
                MATCH (e:Entity)
                %s
                OPTIONAL MATCH (e)-[:MENTIONED_IN]->(d:Document)
                RETURN e.name as name, e.type as type, count(DISTINCT d) as doc_count
                ORDER BY doc_count DESC
                LIMIT 100
            """ % (f"WHERE e.type = '{entity_type}'" if entity_type else "")
            
            with context.neo4j_client.driver.session() as session:
                result = session.run(query)
                
                entities = []
                for record in result:
                    entities.append(Entity(
                        name=record['name'],
                        type=record['type'],
                        document_count=record['doc_count']
                    ))
                
                return entities
        except Exception as e:
            logger.error(f"Error listing entities: {str(e)}")
            raise


# Mutations

@strawberry.type
class Mutation:
    """GraphQL mutations."""
    
    @strawberry.field
    async def process_document(self, file_name: str) -> Document:
        """Process a document from the input directory."""
        try:
            context = Context()
            
            file_path = f"{settings.input_dir}/{file_name}"
            
            # Process document
            doc_data = context.processor.process_document(file_path)
            
            # Generate embeddings
            texts = [chunk['text'] for chunk in doc_data['chunks']]
            embeddings = context.ollama_client.generate_embeddings_batch(texts)
            
            # Index
            document_id = f"{file_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            context.opensearch_client.index_document(
                document_id=document_id,
                file_name=file_name,
                file_path=file_path,
                chunks=doc_data['chunks'],
                embeddings=embeddings,
                metadata=doc_data['metadata']
            )
            
            # Build graph
            context.graph_builder.build_document_graph(
                document_id=document_id,
                file_name=file_name,
                file_path=file_path,
                chunks=doc_data['chunks'],
                metadata=doc_data['metadata']
            )
            
            return Document(
                document_id=document_id,
                metadata=DocumentMetadata(**doc_data['metadata']),
                chunks_count=len(doc_data['chunks']),
                entities_count=len(doc_data.get('entities', []))
            )
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            raise


# Create schema
schema = strawberry.Schema(query=Query, mutation=Mutation)

# Create GraphQL router
graphql_router = GraphQLRouter(schema, path="/api/graphql")

# Made with Bob
