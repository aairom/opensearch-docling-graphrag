"""
Main Streamlit application for OpenSearch-Docling-GraphRAG.
"""
import streamlit as st
from streamlit_option_menu import option_menu
import os
from pathlib import Path
from datetime import datetime
import json
from loguru import logger
import sys

# Configure logger
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("logs/app_{time}.log", rotation="1 day", retention="7 days", level="DEBUG")

# Import application modules
from src.processors import DoclingProcessor
from src.rag import OpenSearchClient, OllamaClient
from src.graphrag import Neo4jClient, GraphBuilder
from config.settings import settings

# Page configuration
st.set_page_config(
    page_title="OpenSearch-Docling-GraphRAG",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'processor' not in st.session_state:
    st.session_state.processor = None
if 'opensearch_client' not in st.session_state:
    st.session_state.opensearch_client = None
if 'ollama_client' not in st.session_state:
    st.session_state.ollama_client = None
if 'neo4j_client' not in st.session_state:
    st.session_state.neo4j_client = None
if 'graph_builder' not in st.session_state:
    st.session_state.graph_builder = None
if 'initialized' not in st.session_state:
    st.session_state.initialized = False


def initialize_clients():
    """Initialize all clients."""
    try:
        with st.spinner("Initializing clients..."):
            if not st.session_state.initialized:
                st.session_state.processor = DoclingProcessor()
                st.session_state.opensearch_client = OpenSearchClient()
                st.session_state.ollama_client = OllamaClient()
                st.session_state.neo4j_client = Neo4jClient()
                st.session_state.graph_builder = GraphBuilder(st.session_state.neo4j_client)
                st.session_state.initialized = True
                st.success("✅ All clients initialized successfully!")
                logger.info("All clients initialized")
    except Exception as e:
        st.error(f"❌ Error initializing clients: {str(e)}")
        logger.error(f"Initialization error: {str(e)}")


def process_single_file(uploaded_file):
    """Process a single uploaded file."""
    try:
        # Save uploaded file temporarily
        temp_path = Path(settings.input_dir) / uploaded_file.name
        with open(temp_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())
        
        # Process document
        with st.spinner(f"Processing {uploaded_file.name}..."):
            doc_data = st.session_state.processor.process_document(str(temp_path))
            
            # Generate embeddings
            texts = [chunk['text'] for chunk in doc_data['chunks']]
            embeddings = st.session_state.ollama_client.generate_embeddings_batch(texts)
            
            # Index in OpenSearch
            document_id = f"{Path(uploaded_file.name).stem}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            st.session_state.opensearch_client.index_document(
                document_id=document_id,
                file_name=uploaded_file.name,
                file_path=str(temp_path),
                chunks=doc_data['chunks'],
                embeddings=embeddings,
                metadata=doc_data['metadata']
            )
            
            # Build knowledge graph
            st.session_state.graph_builder.build_document_graph(
                document_id=document_id,
                file_name=uploaded_file.name,
                file_path=str(temp_path),
                chunks=doc_data['chunks'],
                metadata=doc_data['metadata']
            )
            
            # Save output
            output_file = st.session_state.processor.save_output(doc_data, settings.output_dir)
            
            return {
                'success': True,
                'document_id': document_id,
                'output_file': output_file,
                'chunks': len(doc_data['chunks'])
            }
            
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        return {'success': False, 'error': str(e)}


def process_batch_files():
    """Process all files in the input directory."""
    input_dir = Path(settings.input_dir)
    files = list(input_dir.glob('*'))
    files = [f for f in files if f.is_file() and not f.name.startswith('.')]
    
    if not files:
        st.warning("No files found in input directory")
        return
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    results = []
    
    for i, file_path in enumerate(files):
        status_text.text(f"Processing {file_path.name} ({i+1}/{len(files)})")
        
        try:
            # Process document
            doc_data = st.session_state.processor.process_document(str(file_path))
            
            # Generate embeddings
            texts = [chunk['text'] for chunk in doc_data['chunks']]
            embeddings = st.session_state.ollama_client.generate_embeddings_batch(texts)
            
            # Index in OpenSearch
            document_id = f"{file_path.stem}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            st.session_state.opensearch_client.index_document(
                document_id=document_id,
                file_name=file_path.name,
                file_path=str(file_path),
                chunks=doc_data['chunks'],
                embeddings=embeddings,
                metadata=doc_data['metadata']
            )
            
            # Build knowledge graph
            st.session_state.graph_builder.build_document_graph(
                document_id=document_id,
                file_name=file_path.name,
                file_path=str(file_path),
                chunks=doc_data['chunks'],
                metadata=doc_data['metadata']
            )
            
            # Save output
            output_file = st.session_state.processor.save_output(doc_data, settings.output_dir)
            
            results.append({
                'file': file_path.name,
                'status': 'success',
                'document_id': document_id,
                'chunks': len(doc_data['chunks'])
            })
            
        except Exception as e:
            logger.error(f"Error processing {file_path.name}: {str(e)}")
            results.append({
                'file': file_path.name,
                'status': 'failed',
                'error': str(e)
            })
        
        progress_bar.progress((i + 1) / len(files))
    
    status_text.text("Batch processing complete!")
    return results


def main():
    """Main application."""
    
    # Sidebar
    with st.sidebar:
        st.title("📚 Document RAG System")
        
        selected = option_menu(
            menu_title=None,
            options=["Home", "Upload", "Batch Process", "Search", "Graph Explorer", "Settings"],
            icons=["house", "cloud-upload", "files", "search", "diagram-3", "gear"],
            default_index=0,
        )
        
        st.divider()
        
        # System status
        st.subheader("System Status")
        if st.session_state.initialized:
            st.success("✅ System Ready")
            
            # Show statistics
            try:
                doc_count = st.session_state.opensearch_client.get_document_count()
                st.metric("Indexed Chunks", doc_count)
                
                graph_stats = st.session_state.graph_builder.get_graph_summary()
                st.metric("Documents in Graph", graph_stats.get('total_documents', 0))
                st.metric("Entities", graph_stats.get('total_entities', 0))
            except:
                pass
        else:
            st.warning("⚠️ System Not Initialized")
            if st.button("Initialize System"):
                initialize_clients()
    
    # Main content
    if selected == "Home":
        st.title("🏠 Welcome to OpenSearch-Docling-GraphRAG")
        st.markdown("""
        ### A Comprehensive Document Processing and RAG System
        
        This application combines:
        - **Docling**: Advanced document processing
        - **OpenSearch**: Vector search and retrieval
        - **Neo4j**: Knowledge graph construction
        - **Ollama**: Local LLM for embeddings and generation
        
        #### Features:
        - 📄 Process various document formats (PDF, DOCX, PPTX, etc.)
        - 🔍 Semantic search with vector embeddings
        - 🕸️ Knowledge graph construction and exploration
        - 💬 RAG-based question answering
        - 📊 Batch processing capabilities
        
        #### Getting Started:
        1. Initialize the system using the sidebar button
        2. Upload documents or process batch files
        3. Search and query your documents
        4. Explore the knowledge graph
        """)
        
        if not st.session_state.initialized:
            st.info("👈 Please initialize the system from the sidebar to get started")
    
    elif selected == "Upload":
        st.title("📤 Upload Documents")
        
        if not st.session_state.initialized:
            st.warning("Please initialize the system first")
            return
        
        uploaded_file = st.file_uploader(
            "Choose a document",
            type=['pdf', 'docx', 'pptx', 'txt', 'md', 'html']
        )
        
        if uploaded_file:
            st.info(f"File: {uploaded_file.name} ({uploaded_file.size} bytes)")
            
            if st.button("Process Document"):
                result = process_single_file(uploaded_file)
                
                if result['success']:
                    st.success(f"✅ Document processed successfully!")
                    st.json({
                        'Document ID': result['document_id'],
                        'Chunks Created': result['chunks'],
                        'Output File': result['output_file']
                    })
                else:
                    st.error(f"❌ Error: {result['error']}")
    
    elif selected == "Batch Process":
        st.title("📁 Batch Process Documents")
        
        if not st.session_state.initialized:
            st.warning("Please initialize the system first")
            return
        
        st.info(f"Input directory: {settings.input_dir}")
        
        input_dir = Path(settings.input_dir)
        files = list(input_dir.glob('*'))
        files = [f for f in files if f.is_file() and not f.name.startswith('.')]
        
        st.write(f"Found {len(files)} files:")
        for f in files:
            st.text(f"  • {f.name}")
        
        if st.button("Process All Files"):
            if files:
                results = process_batch_files()
                
                # Display results
                st.subheader("Processing Results")
                success_count = sum(1 for r in results if r['status'] == 'success')
                st.metric("Successfully Processed", f"{success_count}/{len(results)}")
                
                # Show details
                for result in results:
                    if result['status'] == 'success':
                        st.success(f"✅ {result['file']} - {result['chunks']} chunks")
                    else:
                        st.error(f"❌ {result['file']} - {result['error']}")
            else:
                st.warning("No files to process")
    
    elif selected == "Search":
        st.title("🔍 Search Documents")
        
        if not st.session_state.initialized:
            st.warning("Please initialize the system first")
            return
        
        query = st.text_input("Enter your question:")
        k = st.slider("Number of results", 1, 10, 5)
        
        if query and st.button("Search"):
            with st.spinner("Searching..."):
                # Generate query embedding
                query_embedding = st.session_state.ollama_client.generate_embedding(query)
                
                # Search
                results = st.session_state.opensearch_client.search(
                    query_embedding=query_embedding,
                    k=k
                )
                
                # Generate RAG response
                rag_response = st.session_state.ollama_client.generate_rag_response(
                    query=query,
                    retrieved_docs=results
                )
                
                # Display answer
                st.subheader("Answer")
                st.write(rag_response['answer'])
                
                # Display sources
                st.subheader("Sources")
                for i, source in enumerate(rag_response['sources'], 1):
                    with st.expander(f"Source {i}: {source['file_name']} (Score: {source['score']:.4f})"):
                        st.write(f"Chunk ID: {source['chunk_id']}")
    
    elif selected == "Graph Explorer":
        st.title("🕸️ Knowledge Graph Explorer")
        
        if not st.session_state.initialized:
            st.warning("Please initialize the system first")
            return
        
        # Graph statistics
        st.subheader("Graph Statistics")
        stats = st.session_state.graph_builder.get_graph_summary()
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Documents", stats.get('total_documents', 0))
        col2.metric("Chunks", stats.get('total_chunks', 0))
        col3.metric("Entities", stats.get('total_entities', 0))
        col4.metric("Relationships", stats.get('total_relationships', 0))
        
        # Entity search
        st.subheader("Find Entity Connections")
        entity_name = st.text_input("Enter entity name:")
        
        if entity_name and st.button("Find Connections"):
            with st.spinner("Searching graph..."):
                connections = st.session_state.graph_builder.find_connections(entity_name)
                
                st.write(f"Found {connections['connection_count']} related documents:")
                for doc in connections['related_documents']:
                    st.write(f"  • {doc['file_name']} (distance: {doc['distance']})")
    
    elif selected == "Settings":
        st.title("⚙️ Settings")
        
        st.subheader("Configuration")
        st.json({
            'Ollama Model': settings.ollama_model,
            'Embedding Model': settings.ollama_embedding_model,
            'OpenSearch Host': f"{settings.opensearch_host}:{settings.opensearch_port}",
            'Neo4j URI': settings.neo4j_uri,
            'Input Directory': settings.input_dir,
            'Output Directory': settings.output_dir,
            'Chunk Size': settings.chunk_size,
            'Chunk Overlap': settings.chunk_overlap
        })


if __name__ == "__main__":
    main()

# Made with Bob
