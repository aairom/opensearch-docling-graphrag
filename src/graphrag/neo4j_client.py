"""
Neo4j client for graph database operations.
"""
from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase
from loguru import logger

from config.settings import settings


class Neo4jClient:
    """Client for interacting with Neo4j graph database."""
    
    def __init__(self):
        """Initialize Neo4j client."""
        self.driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password)
        )
        self._verify_connectivity()
        logger.info("Neo4j client initialized")
    
    def _verify_connectivity(self):
        """Verify connection to Neo4j."""
        try:
            with self.driver.session() as session:
                session.run("RETURN 1")
            logger.info("Neo4j connection verified")
        except Exception as e:
            logger.error(f"Neo4j connection failed: {str(e)}")
            raise
    
    def close(self):
        """Close the driver connection."""
        self.driver.close()
        logger.info("Neo4j connection closed")
    
    def create_document_node(
        self,
        document_id: str,
        file_name: str,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a document node in the graph.
        
        Args:
            document_id: Unique document identifier
            file_name: Name of the file
            file_path: Path to the file
            metadata: Additional metadata
            
        Returns:
            Created node information
        """
        with self.driver.session() as session:
            query = """
            MERGE (d:Document {id: $document_id})
            SET d.file_name = $file_name,
                d.file_path = $file_path,
                d.metadata = $metadata,
                d.created_at = datetime()
            RETURN d
            """
            result = session.run(
                query,
                document_id=document_id,
                file_name=file_name,
                file_path=file_path,
                metadata=metadata or {}
            )
            record = result.single()
            logger.info(f"Created document node: {document_id}")
            return dict(record["d"])
    
    def create_chunk_node(
        self,
        document_id: str,
        chunk_id: int,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a chunk node and link it to its document.
        
        Args:
            document_id: Parent document identifier
            chunk_id: Chunk identifier
            text: Chunk text
            metadata: Additional metadata
            
        Returns:
            Created node information
        """
        with self.driver.session() as session:
            query = """
            MATCH (d:Document {id: $document_id})
            CREATE (c:Chunk {id: $chunk_id, document_id: $document_id})
            SET c.text = $text,
                c.metadata = $metadata,
                c.created_at = datetime()
            CREATE (d)-[:HAS_CHUNK]->(c)
            RETURN c
            """
            result = session.run(
                query,
                document_id=document_id,
                chunk_id=chunk_id,
                text=text,
                metadata=metadata or {}
            )
            record = result.single()
            return dict(record["c"])
    
    def create_entity_node(
        self,
        entity_name: str,
        entity_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create an entity node.
        
        Args:
            entity_name: Name of the entity
            entity_type: Type of entity (Person, Organization, Location, etc.)
            properties: Additional properties
            
        Returns:
            Created node information
        """
        with self.driver.session() as session:
            query = f"""
            MERGE (e:Entity:{entity_type} {{name: $entity_name}})
            SET e += $properties,
                e.created_at = coalesce(e.created_at, datetime())
            RETURN e
            """
            result = session.run(
                query,
                entity_name=entity_name,
                properties=properties or {}
            )
            record = result.single()
            return dict(record["e"])
    
    def create_relationship(
        self,
        from_node_id: str,
        to_node_id: str,
        relationship_type: str,
        properties: Optional[Dict[str, Any]] = None
    ):
        """
        Create a relationship between two nodes.
        
        Args:
            from_node_id: Source node ID
            to_node_id: Target node ID
            relationship_type: Type of relationship
            properties: Relationship properties
        """
        with self.driver.session() as session:
            query = f"""
            MATCH (a {{id: $from_id}})
            MATCH (b {{id: $to_id}})
            MERGE (a)-[r:{relationship_type}]->(b)
            SET r += $properties
            RETURN r
            """
            session.run(
                query,
                from_id=from_node_id,
                to_id=to_node_id,
                properties=properties or {}
            )
    
    def find_related_documents(
        self,
        entity_name: str,
        max_depth: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Find documents related to an entity.
        
        Args:
            entity_name: Name of the entity
            max_depth: Maximum relationship depth
            
        Returns:
            List of related documents
        """
        with self.driver.session() as session:
            query = """
            MATCH (e:Entity {name: $entity_name})
            MATCH path = (e)-[*1..%d]-(d:Document)
            RETURN DISTINCT d.id as document_id, 
                   d.file_name as file_name,
                   length(path) as distance
            ORDER BY distance
            """ % max_depth
            
            result = session.run(query, entity_name=entity_name)
            return [dict(record) for record in result]
    
    def get_document_graph(self, document_id: str) -> Dict[str, Any]:
        """
        Get the graph structure for a document.
        
        Args:
            document_id: Document identifier
            
        Returns:
            Graph structure with nodes and relationships
        """
        with self.driver.session() as session:
            query = """
            MATCH (d:Document {id: $document_id})
            OPTIONAL MATCH (d)-[r1:HAS_CHUNK]->(c:Chunk)
            OPTIONAL MATCH (c)-[r2]-(e:Entity)
            RETURN d, collect(DISTINCT c) as chunks, 
                   collect(DISTINCT e) as entities,
                   collect(DISTINCT r1) as chunk_rels,
                   collect(DISTINCT r2) as entity_rels
            """
            result = session.run(query, document_id=document_id)
            record = result.single()
            
            if not record:
                return {}
            
            return {
                "document": dict(record["d"]),
                "chunks": [dict(c) for c in record["chunks"] if c],
                "entities": [dict(e) for e in record["entities"] if e],
                "relationships": {
                    "chunks": len([r for r in record["chunk_rels"] if r]),
                    "entities": len([r for r in record["entity_rels"] if r])
                }
            }
    
    def delete_document(self, document_id: str):
        """
        Delete a document and all its related nodes.
        
        Args:
            document_id: Document identifier
        """
        with self.driver.session() as session:
            query = """
            MATCH (d:Document {id: $document_id})
            OPTIONAL MATCH (d)-[:HAS_CHUNK]->(c:Chunk)
            DETACH DELETE d, c
            """
            session.run(query, document_id=document_id)
            logger.info(f"Deleted document from graph: {document_id}")
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Get database statistics.
        
        Returns:
            Statistics dictionary
        """
        with self.driver.session() as session:
            query = """
            MATCH (d:Document) WITH count(d) as docs
            MATCH (c:Chunk) WITH docs, count(c) as chunks
            MATCH (e:Entity) WITH docs, chunks, count(e) as entities
            MATCH ()-[r]->() WITH docs, chunks, entities, count(r) as relationships
            RETURN docs, chunks, entities, relationships
            """
            result = session.run(query)
            record = result.single()
            
            return {
                "documents": record["docs"],
                "chunks": record["chunks"],
                "entities": record["entities"],
                "relationships": record["relationships"]
            }

# Made with Bob
