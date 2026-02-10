# Troubleshooting Guide

## Python 3.14 Compatibility Issue

### Problem
You're seeing this error:
```
error: the configured Python interpreter version (3.14) is newer than PyO3's maximum supported version (3.13)
```

### Root Cause
Python 3.14 is installed and being used by the virtual environment, but pydantic-core (required by pydantic) doesn't support Python 3.14 yet.

### Solution

**Option 1: Install Python 3.11, 3.12, or 3.13**

Using Homebrew (recommended):
```bash
# Install Python 3.11
brew install python@3.11

# Verify installation
/opt/homebrew/bin/python3.11 --version

# Remove old venv
cd /Users/alainairom/Devs/opensearch-docling-graphrag
rm -rf venv

# Create venv with specific Python version
/opt/homebrew/bin/python3.11 -m venv venv

# Activate and install
source venv/bin/activate
pip install -r requirements.txt
```

**Option 2: Use pyenv to manage Python versions**

```bash
# Install pyenv
brew install pyenv

# Install Python 3.11
pyenv install 3.11.7

# Set local Python version for this project
cd /Users/alainairom/Devs/opensearch-docling-graphrag
pyenv local 3.11.7

# Remove old venv
rm -rf venv

# Create new venv
python -m venv venv

# Activate and install
source venv/bin/activate
pip install -r requirements.txt
```

**Option 3: Use Docker (bypasses Python version issues)**

```bash
# Use Docker Compose instead
docker-compose up -d

# Access application at http://localhost:8501
```

### Verification

After creating the venv, verify the Python version:
```bash
source venv/bin/activate
python --version  # Should show 3.11.x, 3.12.x, or 3.13.x
```

### Why This Happens

1. Python 3.14 is very new (released in 2026)
2. Many Python packages with C/Rust extensions (like pydantic-core) haven't been updated yet
3. The PyO3 library (used by pydantic-core) currently supports up to Python 3.13

### Alternative: Use Docker

If you can't install an older Python version, use Docker:

```bash
# Build and run with Docker
docker-compose up -d

# The Docker image uses Python 3.11 internally
# No need to manage Python versions on your host
```

## Other Common Issues

### Port Already in Use

**Problem:** Port 8501, 9200, or 7687 already in use

**Solution:**
```bash
# Find process using port
lsof -i :8501

# Kill process
kill -9 <PID>

# Or change port in .env
APP_PORT=8502
```

### Docker Not Running

**Problem:** Docker commands fail

**Solution:**
```bash
# Start Docker Desktop
open -a Docker

# Wait for Docker to start, then try again
docker-compose up -d
```

### Ollama Not Found

**Problem:** Cannot connect to Ollama

**Solution:**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not, start Ollama
ollama serve

# Pull required models
ollama pull ibm/granite4:latest
ollama pull granite-embedding:278m
```

### Out of Memory

**Problem:** System runs out of memory

**Solution:**
```bash
# Reduce batch size in .env
BATCH_SIZE=5
CHUNK_SIZE=256

# Or increase Docker memory limit
# Docker Desktop > Settings > Resources > Memory
```

### Dependencies Won't Install

**Problem:** pip install fails

**Solution:**
```bash
# Upgrade pip
pip install --upgrade pip

# Install with verbose output
pip install -v -r requirements.txt

# If specific package fails, try installing separately
pip install docling
pip install opensearch-py
pip install neo4j
```

## Getting Help

1. Check logs: `tail -f logs/app_*.log`
2. Verify services: `docker-compose ps`
3. Check Python version: `python --version`
4. Review documentation in `docs/` directory

## Quick Reset

If all else fails, start fresh:

```bash
# Stop everything
./stop.sh
docker-compose down -v

# Remove virtual environment
rm -rf venv

# Remove output and logs
rm -rf output/* logs/*

# Start with Docker (recommended)
docker-compose up -d

## Podman Support

### Using Podman Instead of Docker

The application now supports both Docker and Podman. If you have Podman Desktop running:

**Ensure Podman Machine is Started:**
```bash
# Check if podman machine is running
podman machine list

# Start podman machine if not running
podman machine start

# Verify podman is working
podman info
```

**Install podman-compose (if needed):**
```bash
pip install podman-compose
```

**Run the Application:**
```bash
# The start.sh script will automatically detect Podman
./start.sh

# Or use podman-compose directly
podman-compose up -d
```

**Note:** The scripts (start.sh and stop.sh) automatically detect whether you're using Docker or Podman and use the appropriate commands.