#!/bin/bash

# Full Rebuild - NO CACHE
# Use this only when you have problems or want a completely fresh build
# This is SLOW - rebuilds everything from scratch

set -e

echo "🔨 Full Rebuild (NO CACHE - SLOW)..."
echo "====================================="
echo ""
echo "⚠️  WARNING: This will rebuild everything from scratch!"
echo "⚠️  Use quick-rebuild.sh instead for faster rebuilds"
echo ""
read -p "Continue with full rebuild? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cancelled"
    exit 1
fi

# Stop containers
echo ""
echo "1️⃣  Stopping containers..."
docker compose stop

# Remove containers
echo ""
echo "2️⃣  Removing old containers..."
docker compose rm -f

# Rebuild without cache (SLOW)
echo ""
echo "3️⃣  Rebuilding from scratch (this will take a while)..."
docker compose build --no-cache

# Start containers
echo ""
echo "4️⃣  Starting containers..."
docker compose up -d

# Wait for services
echo ""
echo "⏳ Waiting for services..."
sleep 5

# Show logs
echo ""
echo "📋 Recent logs:"
docker compose logs --tail=20

# Show status
echo ""
echo "📊 Container Status:"
docker compose ps

echo ""
echo "✅ Full rebuild complete!"
echo ""
echo "🌐 Access:"
echo "   - Frontend:  http://localhost:5173"
echo "   - Backend:   http://localhost:8000"
echo ""
