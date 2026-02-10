#!/bin/bash

# Stop script for OpenSearch-Docling-GraphRAG application

set -e

echo "🛑 Stopping OpenSearch-Docling-GraphRAG Application..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Stop Streamlit
if [ -f .streamlit.pid ]; then
    STREAMLIT_PID=$(cat .streamlit.pid)
    if ps -p $STREAMLIT_PID > /dev/null 2>&1; then
        echo "🛑 Stopping Streamlit (PID: $STREAMLIT_PID)..."
        kill $STREAMLIT_PID
        echo -e "${GREEN}✅ Streamlit stopped${NC}"
    else
        echo -e "${YELLOW}⚠️  Streamlit process not found${NC}"
    fi
    rm -f .streamlit.pid
else
    echo -e "${YELLOW}⚠️  No Streamlit PID file found${NC}"
    # Try to find and kill streamlit processes
    STREAMLIT_PIDS=$(pgrep -f "streamlit run app.py" || true)
    if [ ! -z "$STREAMLIT_PIDS" ]; then
        echo "🛑 Found Streamlit processes: $STREAMLIT_PIDS"
        kill $STREAMLIT_PIDS
        echo -e "${GREEN}✅ Streamlit processes stopped${NC}"
    fi
fi

# Stop Docker services
if [ -f "docker-compose.yml" ]; then
    echo "🐳 Stopping Docker services..."
    docker-compose down
    echo -e "${GREEN}✅ Docker services stopped${NC}"
else
    echo -e "${YELLOW}⚠️  docker-compose.yml not found. Skipping Docker services...${NC}"
fi

echo ""
echo -e "${GREEN}✅ Application stopped successfully!${NC}"
echo ""
echo "ℹ️  Note: Ollama is still running. Stop it manually if needed:"
echo "   (Ollama typically runs as a system service)"

# Made with Bob
