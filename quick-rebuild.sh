#!/bin/bash

# Quick Rebuild - WITH CACHE
# Use this when you change dependencies but want to reuse cached layers
# Much faster than full rebuild

set -e

echo "🚀 Quick Rebuild (with cache)..."
echo "================================="

# Stop containers
echo "1️⃣  Stopping containers..."
docker compose stop

# Rebuild WITH cache (much faster)
echo ""
echo "2️⃣  Rebuilding with cache..."
docker compose build

# Start containers
echo ""
echo "3️⃣  Starting containers..."
docker compose up -d

# Wait for services
echo ""
echo "⏳ Waiting for services..."
sleep 5

# Show status
echo ""
echo "📊 Container Status:"
docker compose ps

echo ""
echo "✅ Quick rebuild complete!"
echo ""
echo "💡 This rebuild used cached layers for unchanged steps"
echo "   - Cached: Base images, system packages"
echo "   - Rebuilt: Only changed dependencies and code"
echo ""
echo "🌐 Access:"
echo "   - Frontend:  http://localhost:5173"
echo "   - Backend:   http://localhost:8000"
echo ""
