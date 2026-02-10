"""
Document processing handler for job queue.
Wraps document processing logic to work with background job system.
"""
from typing import Dict, Any
from pathlib import Path
from loguru import logger
import uuid

from src.processors import DoclingProcessor
from src.rag import OpenSearchClient, OllamaClient
from src.graphrag import GraphBuilder


def process_document_job(
    job_id: str,
    payload: Dict[str, Any],
    job_manager
) -> Dict[str, Any]:
    """
    Process a document as a background job.
    
    Args:
        job_id: Job ID
        payload: Job payload containing:
            - file_path: Path to document
            - file_name: Original filename
            - document_id: Optional document ID
        job_manager: JobManager instance for progress updates
        
    Returns:
        Processing result
    """
    try:
        # Extract payload
        file_path = payload['file_path']
        file_name = payload['file_name']
        document_id = payload.get('document_id', str(uuid.uuid4()))
        
        logger.info(f"Job {job_id}: Processing document {file_name}")
        
        # Initialize clients (reuse from session state if available)
        docling_processor = DoclingProcessor()
        opensearch_client = OpenSearchClient()
        ollama_client = OllamaClient()
        
        # Import here to avoid circular dependency
        from src.graphrag import Neo4jClient
        neo4j_client = Neo4jClient()
        graph_builder = GraphBuilder(neo4j_client)
        
        # Step 1: Process document with Docling (30%)
        job_manager.update_job_status(job_id, job_manager.JobStatus.PROCESSING, progress=10)
        logger.info(f"Job {job_id}: Step 1 - Processing with Docling")
        
        doc_data = docling_processor.process_document(file_path)
        
        job_manager.update_job_status(job_id, job_manager.JobStatus.PROCESSING, progress=30)
        
        # Step 2: Generate embeddings (50%)
        logger.info(f"Job {job_id}: Step 2 - Generating embeddings")
        
        embeddings = []
        for chunk in doc_data['chunks']:
            embedding = ollama_client.generate_embedding(chunk['text'])
            embeddings.append(embedding)
        
        job_manager.update_job_status(job_id, job_manager.JobStatus.PROCESSING, progress=50)
        
        # Step 3: Store in OpenSearch (70%)
        logger.info(f"Job {job_id}: Step 3 - Storing in OpenSearch")
        
        opensearch_client.index_document(
            document_id=document_id,
            file_name=file_name,
            file_path=file_path,
            chunks=doc_data['chunks'],
            embeddings=embeddings,
            metadata=doc_data['metadata']
        )
        
        job_manager.update_job_status(job_id, job_manager.JobStatus.PROCESSING, progress=70)
        
        # Step 4: Build knowledge graph (90%)
        logger.info(f"Job {job_id}: Step 4 - Building knowledge graph")
        
        graph_builder.build_document_graph(
            document_id=document_id,
            file_name=file_name,
            file_path=file_path,
            chunks=doc_data['chunks'],
            metadata=doc_data['metadata']
        )
        
        job_manager.update_job_status(job_id, job_manager.JobStatus.PROCESSING, progress=90)
        
        # Step 5: Save output (95%)
        logger.info(f"Job {job_id}: Step 5 - Saving output")
        
        output_file = docling_processor.save_output(doc_data, "output")
        
        job_manager.update_job_status(job_id, job_manager.JobStatus.PROCESSING, progress=95)
        
        # Cleanup
        neo4j_client.close()
        
        # Return result
        result = {
            'document_id': document_id,
            'file_name': file_name,
            'output_file': output_file,
            'num_chunks': len(doc_data['chunks']),
            'metadata': doc_data['metadata']
        }
        
        logger.success(f"Job {job_id}: Document processed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Job {job_id}: Error processing document - {str(e)}")
        raise


def process_batch_job(
    job_id: str,
    payload: Dict[str, Any],
    job_manager
) -> Dict[str, Any]:
    """
    Process multiple documents as a batch job.
    
    Args:
        job_id: Job ID
        payload: Job payload containing:
            - input_dir: Directory with documents
        job_manager: JobManager instance
        
    Returns:
        Batch processing result
    """
    try:
        input_dir = Path(payload['input_dir'])
        
        # Get all files
        files = []
        for ext in ['*.pdf', '*.docx', '*.pptx', '*.html', '*.md', '*.txt']:
            files.extend(input_dir.glob(ext))
        
        if not files:
            return {
                'processed': 0,
                'failed': 0,
                'message': 'No documents found'
            }
        
        total_files = len(files)
        processed = 0
        failed = 0
        results = []
        
        logger.info(f"Job {job_id}: Processing {total_files} documents")
        
        for i, file_path in enumerate(files):
            try:
                # Update progress
                progress = int((i / total_files) * 100)
                job_manager.update_job_status(
                    job_id,
                    job_manager.JobStatus.PROCESSING,
                    progress=progress
                )
                
                # Process document
                doc_payload = {
                    'file_path': str(file_path),
                    'file_name': file_path.name,
                    'document_id': str(uuid.uuid4())
                }
                
                result = process_document_job(job_id, doc_payload, job_manager)
                results.append({
                    'file': file_path.name,
                    'status': 'success',
                    'document_id': result['document_id']
                })
                processed += 1
                
            except Exception as e:
                logger.error(f"Job {job_id}: Failed to process {file_path.name} - {str(e)}")
                results.append({
                    'file': file_path.name,
                    'status': 'failed',
                    'error': str(e)
                })
                failed += 1
        
        return {
            'total': total_files,
            'processed': processed,
            'failed': failed,
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Job {job_id}: Batch processing error - {str(e)}")
        raise


# Made with Bob