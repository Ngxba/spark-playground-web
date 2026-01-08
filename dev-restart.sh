#!/bin/bash

# Fast Development Restart - NO REBUILD
# Use this for most code changes (Python/JavaScript files)
# Changes are picked up via volume mounts + hot reload

set -e

echo "⚡ Fast Development Restart (No Rebuild)..."
echo "==========================================="

# Just restart containers (keeps images, uses volume mounts)
echo "🔄 Restarting containers..."
docker compose restart

# Wait a moment for services to restart
sleep 3

# Show status
echo ""
echo "📊 Container Status:"
docker compose ps

echo ""
echo "✅ Containers restarted! (No rebuild - using cached images)"
echo ""
echo "🔥 Hot Reload Status:"
echo "   - Backend:  ✅ Uvicorn --reload is active"
echo "   - Frontend: ✅ Vite HMR is active"
echo ""
echo "💡 Code changes should appear automatically via:"
echo "   - Volume mounts (./backend/app → /app/app)"
echo "   - Volume mounts (./frontend → /app)"
echo "   - Hot reload for both services"
echo ""
echo "🌐 Access:"
echo "   - Frontend:  http://localhost:5173"
echo "   - Backend:   http://localhost:8000"
echo ""
echo "📋 If changes don't appear, check logs:"
echo "   docker compose logs -f backend"
echo "   docker compose logs -f frontend"
echo ""
