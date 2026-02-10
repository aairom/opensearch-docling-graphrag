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

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Start services with docker-compose
if [ -f "docker-compose.yml" ]; then
    echo "🐳 Starting Docker services..."
    docker-compose up -d
    
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
