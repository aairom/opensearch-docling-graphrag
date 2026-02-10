#!/bin/bash

# Start script for OpenSearch-Docling-GraphRAG application
# This script starts all required services and the Streamlit application

set -e

echo "🚀 Starting OpenSearch-Docling-GraphRAG Application..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if .env file exists, if not copy from .env.example
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from .env.example...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✅ .env file created. Please update it with your configuration.${NC}"
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p input output logs

# Check Python version
PYTHON_CMD=""
for cmd in python3.11 python3.12 python3.13 python3; do
    if command -v $cmd &> /dev/null; then
        VERSION=$($cmd --version 2>&1 | awk '{print $2}')
        MAJOR=$(echo $VERSION | cut -d. -f1)
        MINOR=$(echo $VERSION | cut -d. -f2)
        if [ "$MAJOR" -eq 3 ] && [ "$MINOR" -ge 11 ] && [ "$MINOR" -le 13 ]; then
            PYTHON_CMD=$cmd
            echo -e "${GREEN}✅ Found compatible Python: $VERSION${NC}"
            break
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo -e "${RED}❌ Python 3.11-3.13 required. Found incompatible version.${NC}"
    echo "   Please install Python 3.11, 3.12, or 3.13"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Creating...${NC}"
    $PYTHON_CMD -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Detect container runtime (Docker or Podman)
CONTAINER_CMD=""
COMPOSE_CMD=""

if command -v docker &> /dev/null && docker info > /dev/null 2>&1; then
    CONTAINER_CMD="docker"
    COMPOSE_CMD="docker-compose"
    echo -e "${GREEN}✅ Using Docker${NC}"
elif command -v podman &> /dev/null && podman info > /dev/null 2>&1; then
    CONTAINER_CMD="podman"
    COMPOSE_CMD="podman-compose"
    echo -e "${GREEN}✅ Using Podman${NC}"
    
    # Check if podman-compose is installed
    if ! command -v podman-compose &> /dev/null; then
        echo -e "${YELLOW}⚠️  podman-compose not found. Installing...${NC}"
        pip install podman-compose
    fi
else
    echo -e "${RED}❌ Neither Docker nor Podman is running. Please start one of them first.${NC}"
    echo "   For Podman: Make sure Podman Desktop is running and podman machine is started"
    echo "   Run: podman machine start"
    exit 1
fi

# Start services with container runtime
if [ -f "docker-compose.yml" ]; then
    echo "🐳 Starting container services (OpenSearch, Neo4j)..."
    $COMPOSE_CMD up -d
    
    # Wait for services to be ready
    echo "⏳ Waiting for services to be ready..."
    sleep 10
    
    # Check OpenSearch
    echo "🔍 Checking OpenSearch..."
    until curl -s -u admin:admin http://localhost:9200 > /dev/null 2>&1; do
        echo "   Waiting for OpenSearch..."
        sleep 2
    done
    echo -e "${GREEN}✅ OpenSearch is ready${NC}"
    
    # Check Neo4j
    echo "🔍 Checking Neo4j..."
    until curl -s http://localhost:7474 > /dev/null 2>&1; do
        echo "   Waiting for Neo4j..."
        sleep 2
    done
    echo -e "${GREEN}✅ Neo4j is ready${NC}"
else
    echo -e "${YELLOW}⚠️  docker-compose.yml not found. Assuming services are already running...${NC}"
fi

# Check if Ollama is running
echo "🔍 Checking Ollama..."
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${RED}❌ Ollama is not running. Please start Ollama first.${NC}"
    echo "   Run: ollama serve"
    exit 1
fi
echo -e "${GREEN}✅ Ollama is ready${NC}"

# Get the host IP for display
HOST_IP=$(hostname -I | awk '{print $1}')
if [ -z "$HOST_IP" ]; then
    HOST_IP="localhost"
fi

# Start Streamlit in background
echo "🌐 Starting Streamlit application..."
nohup streamlit run app.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --server.headless=true \
    > logs/streamlit.log 2>&1 &

STREAMLIT_PID=$!
echo $STREAMLIT_PID > .streamlit.pid

# Wait for Streamlit to start
echo "⏳ Waiting for Streamlit to start..."
sleep 5

# Check if Streamlit is running
if ps -p $STREAMLIT_PID > /dev/null; then
    echo -e "${GREEN}✅ Streamlit started successfully!${NC}"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${GREEN}🎉 Application is running!${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo -e "📱 Access the application at:"
    echo -e "   ${GREEN}Local:${NC}    http://localhost:8501"
    echo -e "   ${GREEN}Network:${NC}  http://${HOST_IP}:8501"
    echo ""
    echo -e "📊 Service URLs:"
    echo -e "   ${GREEN}OpenSearch:${NC} http://localhost:9200"
    echo -e "   ${GREEN}Neo4j:${NC}      http://localhost:7474"
    echo -e "   ${GREEN}Ollama:${NC}     http://localhost:11434"
    echo ""
    echo -e "🔧 Container Runtime: ${GREEN}$CONTAINER_CMD${NC}"
    echo ""
    echo -e "📝 Logs:"
    echo -e "   ${GREEN}Application:${NC} tail -f logs/streamlit.log"
    echo -e "   ${GREEN}App logs:${NC}    tail -f logs/app_*.log"
    echo ""
    echo -e "🛑 To stop the application, run: ${YELLOW}./stop.sh${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
else
    echo -e "${RED}❌ Failed to start Streamlit. Check logs/streamlit.log for details.${NC}"
    exit 1
fi

# Made with Bob
