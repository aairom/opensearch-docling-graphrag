"""
Graph builder for creating knowledge graphs from documents.
"""
from typing import List, Dict, Any, Optional
import re
from loguru import logger

from .neo4j_client import Neo4jClient


class GraphBuilder:
    """Build knowledge graphs from processed documents."""
    
    def __init__(self, neo4j_client: Neo4jClient):
        """
        Initialize graph builder.
        
        Args:
            neo4j_client: Neo4j client instance
        """
        self.neo4j_client = neo4j_client
        logger.info("Graph builder initialized")
    
    def build_document_graph(
        self,
        document_id: str,
        file_name: str,
        file_path: str,
        chunks: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Build a graph for a document.
        
        Args:
            document_id: Unique document identifier
            file_name: Name of the file
            file_path: Path to the file
            chunks: List of document chunks
            metadata: Additional metadata
        """
        try:
            # Create document node
            self.neo4j_client.create_document_node(
                document_id=document_id,
                file_name=file_name,
                file_path=file_path,
                metadata=metadata
            )
            
            # Create chunk nodes
            for chunk in chunks:
                chunk_id = chunk.get('chunk_id', 0)
                text = chunk.get('text', '')
                
                self.neo4j_client.create_chunk_node(
                    document_id=document_id,
                    chunk_id=chunk_id,
                    text=text,
                    metadata={
                        'start_pos': chunk.get('start_pos'),
                        'end_pos': chunk.get('end_pos'),
                        'length': chunk.get('length')
                    }
                )
                
                # Extract and create entity nodes
                entities = self._extract_entities(text)
                for entity in entities:
                    self._create_entity_and_link(
                        entity=entity,
                        chunk_id=f"{document_id}_chunk_{chunk_id}"
                    )
            
            logger.success(f"Built graph for document: {document_id}")
            
        except Exception as e:
            logger.error(f"Error building graph for {document_id}: {str(e)}")
            raise
    
    def _extract_entities(self, text: str) -> List[Dict[str, str]]:
        """
        Extract entities from text using simple pattern matching.
        In production, use NER models for better accuracy.
        
        Args:
            text: Text to extract entities from
            
        Returns:
            List of entities with their types
        """
        entities = []
        
        # Simple capitalized word patterns (basic NER)
        # In production, use spaCy, transformers, or similar
        
        # Extract potential person names (capitalized words)
        person_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b'
        persons = re.findall(person_pattern, text)
        for person in set(persons):
            entities.append({
                'name': person,
                'type': 'Person'
            })
        
        # Extract potential organizations (words with Inc, Corp, Ltd, etc.)
        org_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Inc|Corp|Ltd|LLC|Company|Corporation)\b'
        orgs = re.findall(org_pattern, text)
        for org in set(orgs):
            entities.append({
                'name': org,
                'type': 'Organization'
            })
        
        # Extract dates
        date_pattern = r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b'
        dates = re.findall(date_pattern, text)
        for date in set(dates):
            entities.append({
                'name': date,
                'type': 'Date'
            })
        
        # Extract email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        for email in set(emails):
            entities.append({
                'name': email,
                'type': 'Email'
            })
        
        # Extract URLs
        url_pattern = r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)'
        urls = re.findall(url_pattern, text)
        for url in set(urls):
            entities.append({
                'name': url,
                'type': 'URL'
            })
        
        return entities
    
    def _create_entity_and_link(self, entity: Dict[str, str], chunk_id: str):
        """
        Create entity node and link it to a chunk.
        
        Args:
            entity: Entity information
            chunk_id: Chunk identifier to link to
        """
        try:
            # Create entity node
            entity_node = self.neo4j_client.create_entity_node(
                entity_name=entity['name'],
                entity_type=entity['type']
            )
            
            # Create relationship between chunk and entity
            self.neo4j_client.create_relationship(
                from_node_id=chunk_id,
                to_node_id=entity['name'],
                relationship_type='MENTIONS',
                properties={'entity_type': entity['type']}
            )
            
        except Exception as e:
            logger.warning(f"Could not create entity {entity['name']}: {str(e)}")
    
    def find_connections(
        self,
        entity_name: str,
        max_depth: int = 2
    ) -> Dict[str, Any]:
        """
        Find connections for an entity across documents.
        
        Args:
            entity_name: Name of the entity
            max_depth: Maximum relationship depth
            
        Returns:
            Connection information
        """
        try:
            related_docs = self.neo4j_client.find_related_documents(
                entity_name=entity_name,
                max_depth=max_depth
            )
            
            return {
                'entity': entity_name,
                'related_documents': related_docs,
                'connection_count': len(related_docs)
            }
            
        except Exception as e:
            logger.error(f"Error finding connections for {entity_name}: {str(e)}")
            raise
    
    def get_graph_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics of the knowledge graph.
        
        Returns:
            Graph statistics
        """
        try:
            stats = self.neo4j_client.get_statistics()
            return {
                'total_documents': stats['documents'],
                'total_chunks': stats['chunks'],
                'total_entities': stats['entities'],
                'total_relationships': stats['relationships'],
                'avg_chunks_per_doc': stats['chunks'] / max(stats['documents'], 1),
                'avg_entities_per_doc': stats['entities'] / max(stats['documents'], 1)
            }
        except Exception as e:
            logger.error(f"Error getting graph summary: {str(e)}")
            return {}

# Made with Bob
