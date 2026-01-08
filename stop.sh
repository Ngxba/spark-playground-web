#!/bin/bash

# Stop Spark Playground - Docker Compose
# This script stops all running containers

set -e  # Exit on error

echo "🛑 Stopping Spark Playground..."
echo "================================"

# Check if docker-compose.yml exists
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: docker-compose.yml not found in current directory"
    echo "Please run this script from the project root directory"
    exit 1
fi

# Stop containers
echo "📦 Stopping containers..."
docker compose stop

echo ""
echo "📊 Container Status:"
docker compose ps

echo ""
echo "✅ Spark Playground stopped successfully!"
echo ""
echo "💡 To remove containers completely, run:"
echo "   docker compose down"
echo ""
echo "💡 To remove containers and volumes, run:"
echo "   docker compose down -v"
echo ""
