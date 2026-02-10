#!/bin/bash

# Fix Podman connection issue
# This script sets the correct default Podman connection

echo "🔧 Fixing Podman connection..."

# Set podman-machine-default as the default connection
podman system connection default podman-machine-default

# Verify it works
if podman info > /dev/null 2>&1; then
    echo "✅ Podman connection fixed successfully!"
    echo ""
    echo "Current connections:"
    podman system connection list
else
    echo "❌ Podman connection still not working"
    echo "Please check if podman machine is running:"
    echo "  podman machine list"
    echo "  podman machine start"
fi

# Made with Bob
