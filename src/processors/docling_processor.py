"""
Document processor using Docling library.
Handles various document formats (PDF, DOCX, PPTX, etc.)
"""
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
from datetime import datetime
from loguru import logger

from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend


class DoclingProcessor:
    """Process documents using Docling library."""
    
    def __init__(self):
        """Initialize the Docling processor."""
        # Configure pipeline options
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = True
        pipeline_options.do_table_structure = True
        
        # Initialize document converter
        self.converter = DocumentConverter(
            allowed_formats=[
                InputFormat.PDF,
                InputFormat.DOCX,
                InputFormat.PPTX,
                InputFormat.HTML,
                InputFormat.IMAGE,
                InputFormat.ASCIIDOC,
                InputFormat.MD,
            ],
            pdf_backend=PyPdfiumDocumentBackend,
            pipeline_options=pipeline_options,
        )
        logger.info("Docling processor initialized")
    
    def process_document(self, file_path: str) -> Dict[str, Any]:
        """
        Process a single document.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Dictionary containing processed document data
        """
        try:
            logger.info(f"Processing document: {file_path}")
            
            # Convert document
            result = self.converter.convert(file_path)
            
            # Extract content
            document_data = {
                "file_path": file_path,
                "file_name": Path(file_path).name,
                "processed_at": datetime.utcnow().isoformat(),
                "content": result.document.export_to_markdown(),
                "metadata": {
                    "num_pages": len(result.document.pages) if hasattr(result.document, 'pages') else 0,
                    "format": Path(file_path).suffix,
                },
                "chunks": [],
            }
            
            # Extract text chunks for embedding
            text_content = result.document.export_to_markdown()
            document_data["chunks"] = self._create_chunks(text_content)
            
            logger.success(f"Successfully processed: {file_path}")
            return document_data
            
        except Exception as e:
            logger.error(f"Error processing document {file_path}: {str(e)}")
            raise
    
    def process_batch(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """
        Process multiple documents in batch.
        
        Args:
            file_paths: List of file paths to process
            
        Returns:
            List of processed document data
        """
        results = []
        for file_path in file_paths:
            try:
                result = self.process_document(file_path)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process {file_path}: {str(e)}")
                results.append({
                    "file_path": file_path,
                    "error": str(e),
                    "processed_at": datetime.utcnow().isoformat(),
                })
        
        return results
    
    def _create_chunks(
        self, 
        text: str, 
        chunk_size: int = 512, 
        overlap: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Split text into overlapping chunks.
        
        Args:
            text: Text to split
            chunk_size: Size of each chunk in characters
            overlap: Overlap between chunks
            
        Returns:
            List of text chunks with metadata
        """
        chunks = []
        start = 0
        chunk_id = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk_text = text[start:end]
            
            chunks.append({
                "chunk_id": chunk_id,
                "text": chunk_text,
                "start_pos": start,
                "end_pos": end,
                "length": len(chunk_text),
            })
            
            start += chunk_size - overlap
            chunk_id += 1
        
        logger.info(f"Created {len(chunks)} chunks from text")
        return chunks
    
    def save_output(self, document_data: Dict[str, Any], output_dir: str) -> str:
        """
        Save processed document data to output directory.
        
        Args:
            document_data: Processed document data
            output_dir: Output directory path
            
        Returns:
            Path to saved output file
        """
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Create timestamped filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        original_name = Path(document_data["file_name"]).stem
        output_file = Path(output_dir) / f"{original_name}_{timestamp}.json"
        
        # Save to JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(document_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved output to: {output_file}")
        return str(output_file)

# Made with Bob
