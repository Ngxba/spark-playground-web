#!/bin/bash

# Restart Spark Playground - Docker Compose
# This script rebuilds and restarts all containers with the latest code

set -e  # Exit on error

echo "🔄 Restarting Spark Playground with latest code..."
echo "==================================================="
echo ""
echo "💡 TIP: For faster restarts, use ./dev-restart.sh instead"
echo "   (no rebuild, just container restart with hot reload)"
echo ""

# Check if docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running. Please start Docker Desktop first."
    exit 1
fi

# Check if docker-compose.yml exists
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: docker-compose.yml not found in current directory"
    echo "Please run this script from the project root directory"
    exit 1
fi

# Stop containers
echo "1️⃣  Stopping existing containers..."
docker compose stop

# Remove containers (keeps volumes)
echo ""
echo "2️⃣  Removing old containers..."
docker compose rm -f

# Rebuild images with latest code (WITH CACHE for speed)
echo ""
echo "3️⃣  Rebuilding images with latest code (using cache)..."
docker compose build

# Start containers
echo ""
echo "4️⃣  Starting containers..."
docker compose up -d

# Wait for services to be healthy
echo ""
echo "⏳ Waiting for services to start..."
sleep 5

# Show logs briefly
echo ""
echo "📋 Recent logs:"
docker compose logs --tail=20

# Check container status
echo ""
echo "📊 Container Status:"
docker compose ps

echo ""
echo "✅ Spark Playground restarted successfully with latest code!"
echo ""
echo "🌐 Access the application:"
echo "   - Frontend:      http://localhost:5173"
echo "   - Backend API:   http://localhost:8000"
echo "   - API Docs:      http://localhost:8000/docs"
echo "   - Spark History: http://localhost:18080"
echo ""
echo "📋 Useful commands:"
echo "   - View logs:     docker compose logs -f"
echo "   - Stop:          ./stop.sh"
echo "   - Clean restart: docker compose down -v && ./restart.sh"
echo ""
