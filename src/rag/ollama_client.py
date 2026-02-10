"""
Ollama client for embeddings and text generation.
"""
from typing import List, Dict, Any, Optional
import ollama
from loguru import logger

from config.settings import settings


class OllamaClient:
    """Client for interacting with Ollama."""
    
    def __init__(self):
        """Initialize Ollama client."""
        self.client = ollama.Client(host=settings.ollama_base_url)
        self.model = settings.ollama_model
        self.embedding_model = settings.ollama_embedding_model
        logger.info(f"Ollama client initialized with model: {self.model}")
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        try:
            response = self.client.embeddings(
                model=self.embedding_model,
                prompt=text
            )
            return response['embedding']
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        embeddings = []
        for text in texts:
            try:
                embedding = self.generate_embedding(text)
                embeddings.append(embedding)
            except Exception as e:
                logger.error(f"Error in batch embedding: {str(e)}")
                embeddings.append([0.0] * 768)  # Fallback to zero vector
        
        logger.info(f"Generated {len(embeddings)} embeddings")
        return embeddings
    
    def generate_response(
        self, 
        prompt: str,
        context: Optional[List[str]] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate text response using LLM.
        
        Args:
            prompt: User prompt
            context: Optional context documents
            system_prompt: Optional system prompt
            
        Returns:
            Generated response
        """
        try:
            # Build messages
            messages = []
            
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            # Add context if provided
            if context:
                context_text = "\n\n".join([f"Document {i+1}:\n{doc}" for i, doc in enumerate(context)])
                messages.append({
                    "role": "system",
                    "content": f"Use the following context to answer the question:\n\n{context_text}"
                })
            
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            # Generate response
            response = self.client.chat(
                model=self.model,
                messages=messages
            )
            
            return response['message']['content']
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise
    
    def generate_rag_response(
        self,
        query: str,
        retrieved_docs: List[Dict[str, Any]],
        max_context_length: int = 4000
    ) -> Dict[str, Any]:
        """
        Generate RAG response with retrieved documents.
        
        Args:
            query: User query
            retrieved_docs: Retrieved documents from vector search
            max_context_length: Maximum context length
            
        Returns:
            Response with answer and sources
        """
        try:
            # Extract context from retrieved documents
            context = []
            sources = []
            total_length = 0
            
            for doc in retrieved_docs:
                text = doc.get('text', '')
                if total_length + len(text) <= max_context_length:
                    context.append(text)
                    sources.append({
                        'file_name': doc.get('file_name'),
                        'chunk_id': doc.get('chunk_id'),
                        'score': doc.get('score')
                    })
                    total_length += len(text)
            
            # Generate response
            system_prompt = """You are a helpful assistant that answers questions based on the provided context.
If the answer cannot be found in the context, say so clearly.
Always cite which document you're referring to when answering."""
            
            answer = self.generate_response(
                prompt=query,
                context=context,
                system_prompt=system_prompt
            )
            
            return {
                "answer": answer,
                "sources": sources,
                "num_sources": len(sources)
            }
            
        except Exception as e:
            logger.error(f"Error generating RAG response: {str(e)}")
            raise
    
    def check_connection(self) -> bool:
        """
        Check if Ollama is accessible.
        
        Returns:
            True if connected, False otherwise
        """
        try:
            self.client.list()
            logger.info("Ollama connection successful")
            return True
        except Exception as e:
            logger.error(f"Ollama connection failed: {str(e)}")
            return False

# Made with Bob
