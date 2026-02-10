# Quick Start Guide

Get up and running with OpenSearch-Docling-GraphRAG in 5 minutes!

## Prerequisites Check

```bash
# Check Python version (need 3.11+)
python3 --version

# Check Docker
docker --version

# Check Ollama
ollama --version
```

## Installation

### 1. Install Ollama Models

```bash
ollama pull ibm/granite4:latest
ollama pull granite-embedding:278m
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env if needed (defaults work for local setup)
```

### 3. Start Application

```bash
./start.sh
```

**That's it!** The application will:
- Create necessary directories
- Set up Python environment
- Install dependencies
- Start Docker services
- Launch the web UI

## Access the Application

Open your browser to: **http://localhost:8501**

## First Steps

1. **Initialize System** - Click the button in the sidebar
2. **Upload a Document** - Go to Upload tab, select a file
3. **Process** - Click "Process Document"
4. **Search** - Go to Search tab, ask a question!

## Quick Commands

```bash
# Start application
./start.sh

# Stop application
./stop.sh

# View logs
tail -f logs/streamlit.log

# Check services
docker-compose ps
```

## Service URLs

- **Application**: http://localhost:8501
- **OpenSearch**: http://localhost:9200
- **Neo4j Browser**: http://localhost:7474
- **OpenSearch Dashboards**: http://localhost:5601

## Troubleshooting

### Application won't start?

```bash
# Check if ports are available
lsof -i :8501
lsof -i :9200
lsof -i :7687

# Restart Docker
docker-compose down
docker-compose up -d
```

### Ollama not connecting?

```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if needed
ollama serve
```

### Out of memory?

```bash
# Reduce batch size in .env
BATCH_SIZE=5
CHUNK_SIZE=256
```

## Next Steps

- Read [README.md](README.md) for full documentation
- Check [docs/USER_GUIDE.md](docs/USER_GUIDE.md) for detailed usage
- Review [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for system design
- See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for production deployment

## Sample Workflow

```bash
# 1. Place documents in input folder
cp ~/Documents/*.pdf ./input/

# 2. Start application
./start.sh

# 3. Open browser to http://localhost:8501

# 4. Go to "Batch Process" tab

# 5. Click "Process All Files"

# 6. Go to "Search" tab and ask questions!
```

## Common Issues

| Issue | Solution |
|-------|----------|
| Port 8501 in use | Change APP_PORT in .env |
| Docker not running | Start Docker Desktop |
| Ollama connection failed | Run `ollama serve` |
| Slow processing | Reduce CHUNK_SIZE in .env |

## Getting Help

- Check logs: `tail -f logs/app_*.log`
- Review documentation in `docs/`
- Check GitHub issues
- Verify all services are running: `docker-compose ps`

---

**Ready to go!** 🚀 Start with `./start.sh` and open http://localhost:8501