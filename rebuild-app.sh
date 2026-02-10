#!/bin/bash

# Quick rebuild script for the application container

echo "🔄 Rebuilding application container..."

# Stop the app container
echo "🛑 Stopping docling-app container..."
podman stop docling-app 2>/dev/null || true

# Remove the app container
echo "🗑️  Removing old container..."
podman rm docling-app 2>/dev/null || true

# Remove the app image to force rebuild
echo "🗑️  Removing old image..."
podman rmi localhost/opensearch-docling-graphrag_app:latest 2>/dev/null || true

# Rebuild and start
echo "🔨 Rebuilding and starting..."
podman-compose up -d --build

echo ""
echo "✅ Rebuild complete!"
echo ""
echo "📊 Check status:"
echo "   podman ps"
echo ""
echo "📝 View logs:"
echo "   podman logs -f docling-app"
echo ""
echo "🌐 Access application:"
echo "   http://localhost:8501"

# Made with Bob
