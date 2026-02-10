# User Guide

Complete guide for using the OpenSearch-Docling-GraphRAG application.

## Table of Contents

- [Getting Started](#getting-started)
- [User Interface Overview](#user-interface-overview)
- [Document Processing](#document-processing)
- [Search and Query](#search-and-query)
- [Knowledge Graph](#knowledge-graph)
- [Advanced Features](#advanced-features)
- [Tips and Best Practices](#tips-and-best-practices)

## Getting Started

### First Time Setup

1. **Start the Application**

```bash
./start.sh
```

2. **Access the UI**

Open your browser and navigate to: http://localhost:8501

3. **Initialize the System**

Click the "Initialize System" button in the sidebar. This will:
- Connect to OpenSearch
- Connect to Neo4j
- Verify Ollama connection
- Initialize all components

## User Interface Overview

### Main Navigation

The application has six main sections accessible from the sidebar:

1. **Home** - Welcome page and system overview
2. **Upload** - Upload and process single documents
3. **Batch Process** - Process multiple documents at once
4. **Search** - Query your documents with AI
5. **Graph Explorer** - Explore the knowledge graph
6. **Settings** - View system configuration

### System Status

The sidebar shows:
- System initialization status
- Number of indexed chunks
- Number of documents in graph
- Number of entities extracted

## Document Processing

### Supported Formats

- **PDF** (.pdf) - Including scanned documents with OCR
- **Microsoft Word** (.docx)
- **Microsoft PowerPoint** (.pptx)
- **HTML** (.html)
- **Markdown** (.md)
- **Plain Text** (.txt)
- **AsciiDoc** (.adoc)
- **Images** (with OCR capability)

### Upload Single Document

1. Navigate to the **Upload** tab
2. Click "Browse files" or drag and drop a document
3. Click "Process Document"
4. Wait for processing to complete

**What Happens:**
- Document is parsed and text extracted
- Content is split into chunks
- Embeddings are generated
- Data is indexed in OpenSearch
- Knowledge graph is built in Neo4j
- Results are saved to `./output` with timestamp

### Batch Processing

1. Place documents in the `./input` directory
2. Navigate to **Batch Process** tab
3. Review the list of files to be processed
4. Click "Process All Files"
5. Monitor progress bar and results

**Tips:**
- Process similar documents together
- Check available disk space
- Monitor system resources during batch processing

### Output Files

Processed documents are saved to `./output` with format:
```
{filename}_{timestamp}.json
```

Example:
```
report_20260210_143022.json
```

Output includes:
- Original file information
- Extracted text content
- Metadata (pages, format, etc.)
- Text chunks with positions
- Processing timestamp

## Search and Query

### Basic Search

1. Navigate to **Search** tab
2. Enter your question in the text box
3. Adjust "Number of results" slider (1-10)
4. Click "Search"

**Example Queries:**
```
What are the main findings in the report?
Summarize the key points about climate change
Who are the authors mentioned in the documents?
What dates are referenced in the contracts?
```

### Understanding Results

**Answer Section:**
- AI-generated response based on retrieved documents
- Synthesizes information from multiple sources
- Cites relevant context

**Sources Section:**
- Shows which documents were used
- Displays relevance scores
- Links to specific chunks

### Advanced Search Tips

1. **Be Specific**
   - ❌ "Tell me about the project"
   - ✅ "What is the project timeline and budget?"

2. **Ask Follow-up Questions**
   - Build on previous queries
   - Reference specific documents

3. **Use Context**
   - Mention document names if known
   - Reference specific sections or topics

## Knowledge Graph

### Graph Statistics

View overall graph metrics:
- Total documents
- Total chunks
- Total entities extracted
- Total relationships

### Entity Search

1. Navigate to **Graph Explorer** tab
2. Enter an entity name (person, organization, location, etc.)
3. Click "Find Connections"

**What You'll See:**
- Related documents
- Connection distance
- Relationship paths

### Entity Types

The system automatically extracts:

- **Persons** - Names of people
- **Organizations** - Companies, institutions
- **Locations** - Places, addresses
- **Dates** - Temporal references
- **Emails** - Email addresses
- **URLs** - Web links

### Use Cases

**1. Find Related Documents**
```
Search for: "John Smith"
Result: All documents mentioning John Smith
```

**2. Discover Connections**
```
Search for: "Acme Corporation"
Result: Documents, people, and events related to Acme
```

**3. Timeline Analysis**
```
Search for dates to build document timelines
```

## Advanced Features

### Custom Chunk Settings

Modify in `.env`:
```bash
CHUNK_SIZE=512        # Characters per chunk
CHUNK_OVERLAP=50      # Overlap between chunks
```

Restart application after changes.

### Model Selection

Choose different Ollama models in `.env`:
```bash
OLLAMA_MODEL=ibm/granite4:latest
OLLAMA_EMBEDDING_MODEL=granite-embedding:278m
```

Available alternatives:
- `embeddinggemma:latest`
- `mxbai-embed-large:latest`
- `nomic-embed-text:latest`

### Batch Size Configuration

For batch processing, adjust:
```bash
BATCH_SIZE=10         # Documents per batch
```

## Tips and Best Practices

### Document Preparation

1. **Clean Documents**
   - Remove unnecessary pages
   - Ensure text is readable
   - Check for corrupted files

2. **Organize Files**
   - Use descriptive filenames
   - Group related documents
   - Remove duplicates

3. **File Size**
   - Optimal: < 10MB per file
   - Large files take longer to process
   - Consider splitting very large documents

### Search Optimization

1. **Query Formulation**
   - Use complete sentences
   - Include relevant keywords
   - Be specific about what you need

2. **Result Interpretation**
   - Check source scores
   - Review multiple sources
   - Verify critical information

3. **Iterative Refinement**
   - Start broad, then narrow down
   - Use follow-up questions
   - Reference specific findings

### Performance Tips

1. **System Resources**
   - Close unnecessary applications
   - Monitor RAM usage
   - Ensure sufficient disk space

2. **Processing Speed**
   - Process during off-peak hours
   - Use batch processing for multiple files
   - Consider upgrading hardware for large workloads

3. **Data Management**
   - Regularly clean output directory
   - Archive old processed files
   - Monitor database sizes

### Troubleshooting

**Problem: Slow Processing**
- Solution: Reduce chunk size, process fewer documents at once

**Problem: Poor Search Results**
- Solution: Try different query phrasing, check if documents are properly indexed

**Problem: System Not Initializing**
- Solution: Check if all services are running (OpenSearch, Neo4j, Ollama)

**Problem: Out of Memory**
- Solution: Reduce batch size, process smaller documents, restart services

## Keyboard Shortcuts

- `Ctrl/Cmd + R` - Refresh page
- `Ctrl/Cmd + K` - Focus search box
- `Esc` - Close modals

## Data Privacy

### Local Processing

All data is processed locally:
- Documents never leave your system
- No external API calls (except Ollama if remote)
- Full control over your data

### Data Storage

- **Input**: `./input` directory
- **Output**: `./output` directory (timestamped)
- **Logs**: `./logs` directory
- **Database**: Docker volumes (OpenSearch, Neo4j)

### Data Deletion

To remove all data:
```bash
# Stop application
./stop.sh

# Remove Docker volumes
docker-compose down -v

# Clear directories
rm -rf output/* logs/*
```

## Exporting Results

### Export Search Results

Results are displayed in the UI. To save:
1. Copy text from answer section
2. Download source documents from output directory

### Export Graph Data

Use Neo4j Browser:
1. Access: http://localhost:7474
2. Login with credentials from `.env`
3. Run Cypher queries to export data

Example query:
```cypher
MATCH (d:Document)-[r]->(e:Entity)
RETURN d.file_name, e.name, type(r)
```

### Export Vector Data

Use OpenSearch Dashboards:
1. Access: http://localhost:5601
2. Navigate to Dev Tools
3. Export using OpenSearch API

## Getting Help

### Documentation

- [README.md](../README.md) - Project overview
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [DEPLOYMENT.md](DEPLOYMENT.md) - Deployment guide
- [k8s/README.md](../k8s/README.md) - Kubernetes guide

### Logs

Check application logs:
```bash
# Streamlit logs
tail -f logs/streamlit.log

# Application logs
tail -f logs/app_*.log
```

### Support

- Check GitHub issues
- Review documentation
- Examine log files
- Test with sample documents

## Appendix

### Sample Queries

**General Information:**
```
What is this document about?
Summarize the main points
List all key findings
```

**Specific Details:**
```
What are the dates mentioned?
Who are the stakeholders?
What is the budget breakdown?
```

**Comparative:**
```
Compare the findings in document A and B
What are the differences between these reports?
How do these proposals differ?
```

**Analytical:**
```
What are the risks identified?
What recommendations are made?
What are the next steps?
```

### Configuration Reference

| Setting | Default | Description |
|---------|---------|-------------|
| CHUNK_SIZE | 512 | Characters per chunk |
| CHUNK_OVERLAP | 50 | Overlap between chunks |
| BATCH_SIZE | 10 | Documents per batch |
| APP_PORT | 8501 | Application port |
| OPENSEARCH_PORT | 9200 | OpenSearch port |
| NEO4J_PORT | 7687 | Neo4j Bolt port |

### Glossary

- **Chunk** - A segment of text from a document
- **Embedding** - Vector representation of text
- **Entity** - Named item extracted from text (person, place, etc.)
- **Graph** - Network of connected entities and documents
- **RAG** - Retrieval-Augmented Generation
- **Vector Search** - Similarity-based search using embeddings