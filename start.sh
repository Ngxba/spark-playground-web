#!/bin/bash

# Start Spark Playground - Docker Compose
# This script starts all containers in detached mode

set -e  # Exit on error

echo "🚀 Starting Spark Playground..."
echo "================================"

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

# Start containers
echo "📦 Starting containers..."
docker compose up -d

# Wait for services to be healthy
echo ""
echo "⏳ Waiting for services to start..."
sleep 5

# Check container status
echo ""
echo "📊 Container Status:"
docker compose ps

echo ""
echo "✅ Spark Playground started successfully!"
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
echo "   - Restart:       ./restart.sh"
echo ""
