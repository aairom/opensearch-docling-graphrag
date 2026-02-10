"""
OpenSearch client for vector storage and retrieval.
"""
from typing import List, Dict, Any, Optional
from opensearchpy import OpenSearch, helpers
from loguru import logger
import json

from config.settings import settings


class OpenSearchClient:
    """Client for interacting with OpenSearch."""
    
    def __init__(self):
        """Initialize OpenSearch client."""
        self.client = OpenSearch(
            hosts=[{
                'host': settings.opensearch_host,
                'port': settings.opensearch_port
            }],
            http_auth=(settings.opensearch_user, settings.opensearch_password),
            use_ssl=settings.opensearch_use_ssl,
            verify_certs=settings.opensearch_verify_certs,
            ssl_show_warn=False
        )
        self.index_name = settings.opensearch_index
        self._ensure_index()
        logger.info(f"OpenSearch client initialized for index: {self.index_name}")
    
    def _ensure_index(self):
        """Create index if it doesn't exist."""
        if not self.client.indices.exists(index=self.index_name):
            index_body = {
                "settings": {
                    "index": {
                        "number_of_shards": 1,
                        "number_of_replicas": 0,
                        "knn": True,
                        "knn.algo_param.ef_search": 100
                    }
                },
                "mappings": {
                    "properties": {
                        "document_id": {"type": "keyword"},
                        "file_name": {"type": "keyword"},
                        "file_path": {"type": "text"},
                        "chunk_id": {"type": "integer"},
                        "text": {"type": "text"},
                        "embedding": {
                            "type": "knn_vector",
                            "dimension": 768,
                            "method": {
                                "name": "hnsw",
                                "space_type": "cosinesimil",
                                "engine": "nmslib",
                                "parameters": {
                                    "ef_construction": 128,
                                    "m": 24
                                }
                            }
                        },
                        "metadata": {"type": "object"},
                        "timestamp": {"type": "date"}
                    }
                }
            }
            self.client.indices.create(index=self.index_name, body=index_body)
            logger.info(f"Created index: {self.index_name}")
    
    def index_document(
        self, 
        document_id: str,
        file_name: str,
        file_path: str,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Index a document with its chunks and embeddings.
        
        Args:
            document_id: Unique document identifier
            file_name: Name of the file
            file_path: Path to the file
            chunks: List of text chunks
            embeddings: List of embedding vectors
            metadata: Additional metadata
            
        Returns:
            Indexing result
        """
        try:
            actions = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                action = {
                    "_index": self.index_name,
                    "_id": f"{document_id}_chunk_{i}",
                    "_source": {
                        "document_id": document_id,
                        "file_name": file_name,
                        "file_path": file_path,
                        "chunk_id": i,
                        "text": chunk.get("text", ""),
                        "embedding": embedding,
                        "metadata": metadata or {},
                        "timestamp": chunk.get("timestamp")
                    }
                }
                actions.append(action)
            
            # Bulk index
            success, failed = helpers.bulk(self.client, actions, raise_on_error=False)
            
            logger.info(f"Indexed {success} chunks for document: {document_id}")
            if failed:
                logger.warning(f"Failed to index {len(failed)} chunks")
            
            return {
                "success": success,
                "failed": len(failed),
                "document_id": document_id
            }
            
        except Exception as e:
            logger.error(f"Error indexing document {document_id}: {str(e)}")
            raise
    
    def search(
        self, 
        query_embedding: List[float],
        k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents using vector similarity.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            filter_dict: Optional filters
            
        Returns:
            List of search results
        """
        try:
            query = {
                "size": k,
                "query": {
                    "knn": {
                        "embedding": {
                            "vector": query_embedding,
                            "k": k
                        }
                    }
                }
            }
            
            # Add filters if provided
            if filter_dict:
                query["query"] = {
                    "bool": {
                        "must": [query["query"]],
                        "filter": [{"term": {k: v}} for k, v in filter_dict.items()]
                    }
                }
            
            response = self.client.search(index=self.index_name, body=query)
            
            results = []
            for hit in response['hits']['hits']:
                results.append({
                    "score": hit['_score'],
                    "document_id": hit['_source']['document_id'],
                    "file_name": hit['_source']['file_name'],
                    "chunk_id": hit['_source']['chunk_id'],
                    "text": hit['_source']['text'],
                    "metadata": hit['_source'].get('metadata', {})
                })
            
            logger.info(f"Found {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Error searching: {str(e)}")
            raise
    
    def delete_document(self, document_id: str) -> Dict[str, Any]:
        """
        Delete all chunks of a document.
        
        Args:
            document_id: Document identifier
            
        Returns:
            Deletion result
        """
        try:
            query = {
                "query": {
                    "term": {
                        "document_id": document_id
                    }
                }
            }
            
            response = self.client.delete_by_query(
                index=self.index_name,
                body=query
            )
            
            logger.info(f"Deleted document: {document_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {str(e)}")
            raise
    
    def get_document_count(self) -> int:
        """Get total number of indexed chunks."""
        try:
            response = self.client.count(index=self.index_name)
            return response['count']
        except Exception as e:
            logger.error(f"Error getting document count: {str(e)}")
            return 0

# Made with Bob
