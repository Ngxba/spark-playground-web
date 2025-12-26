# 🐳 Docker Management Scripts

Quick reference for managing Spark Playground with Docker Compose.

## 📁 Available Scripts

### 1. `./start.sh` - Start the Application

Starts all containers in detached mode.

```bash
./start.sh
```

**What it does:**
- ✅ Checks if Docker is running
- ✅ Starts all containers (spark-history, backend, frontend)
- ✅ Shows container status
- ✅ Displays access URLs

**Access URLs after starting:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Spark History: http://localhost:18080

---

### 2. `./stop.sh` - Stop the Application

Stops all running containers (keeps data).

```bash
./stop.sh
```

**What it does:**
- ✅ Stops all running containers
- ✅ Shows final container status
- ✅ Keeps volumes and data intact

**Note:** Containers are stopped but not removed. Use `docker compose down` to remove them.

---

### 3. `./restart.sh` - Restart with Latest Code

Rebuilds and restarts everything with the latest code changes.

```bash
./restart.sh
```

**What it does:**
- ✅ Stops all containers
- ✅ Removes old containers
- ✅ **Rebuilds images from scratch** (--no-cache)
- ✅ Starts containers with new code
- ✅ Shows recent logs

**Use this when:**
- 🔧 You changed backend Python code
- 🎨 You changed frontend React code
- 📦 You updated dependencies (package.json, requirements.txt)
- 🐛 You want to ensure everything is up-to-date

---

## 🚀 Quick Start

```bash
# First time setup
./start.sh

# Make code changes...
# (edit files in backend/ or frontend/)

# Apply changes
./restart.sh

# When done
./stop.sh
```

---

## 📋 Common Commands

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f spark-history

# Last 50 lines
docker compose logs --tail=50
```

### Container Status

```bash
docker compose ps
```

### Execute Commands in Container

```bash
# Backend shell
docker compose exec backend bash

# Frontend shell
docker compose exec frontend sh

# Run backend tests
docker compose exec backend pytest
```

### Clean Everything

```bash
# Stop and remove containers, networks (keeps volumes)
docker compose down

# Stop and remove containers, networks, AND volumes
docker compose down -v

# Clean restart
docker compose down -v && ./restart.sh
```

### Rebuild Specific Service

```bash
# Rebuild only backend
docker compose build backend
docker compose up -d backend

# Rebuild only frontend
docker compose build frontend
docker compose up -d frontend
```

---

## 🐛 Troubleshooting

### Script Permission Denied

```bash
chmod +x start.sh stop.sh restart.sh
```

### Docker Not Running

```
❌ Error: Docker is not running
```

**Solution:** Start Docker Desktop application.

### Port Already in Use

```
Error: port is already allocated
```

**Solution:**
```bash
# Check what's using the port
lsof -i :5173  # Frontend
lsof -i :8000  # Backend
lsof -i :18080 # Spark History

# Kill the process or change ports in docker-compose.yml
```

### Container Won't Start

```bash
# Check logs
docker compose logs <service-name>

# Example:
docker compose logs backend
```

### Out of Space

```bash
# Clean unused images and containers
docker system prune -a

# Clean everything including volumes
docker system prune -a --volumes
```

### Need Fresh Start

```bash
# Complete clean restart
docker compose down -v
docker system prune -f
./restart.sh
```

---

## 🎯 Development Workflow

### Making Changes to Backend

1. Edit files in `backend/app/`
2. Run `./restart.sh` to rebuild and restart
3. Test at http://localhost:8000

**Hot Reload:** Backend has volume mount, so some changes may appear without restart. But for dependency changes, always run `./restart.sh`.

### Making Changes to Frontend

1. Edit files in `frontend/src/`
2. Changes should appear automatically (Vite hot reload)
3. If not, run `./restart.sh`

### Adding New Dependencies

**Backend (Python):**
```bash
# 1. Add to backend/requirements.txt
# 2. Rebuild
./restart.sh
```

**Frontend (Node):**
```bash
# 1. Add to frontend/package.json
# 2. Rebuild
./restart.sh
```

---

## 📊 Container Overview

| Service | Port | Description |
|---------|------|-------------|
| `frontend` | 5173 | React + Vite development server |
| `backend` | 8000 | FastAPI + PySpark backend |
| `spark-history` | 18080 | Spark History Server UI |

---

## 💡 Tips

1. **Daily Development:**
   - Use `./start.sh` once
   - Make changes
   - Frontend auto-reloads
   - Backend may need `./restart.sh`

2. **Before Committing:**
   - Run `./restart.sh` to ensure clean build
   - Test all functionality
   - Check logs for errors

3. **Performance:**
   - `./start.sh` is fast (uses existing images)
   - `./restart.sh` is slow (rebuilds everything)
   - Only use `./restart.sh` when code changes need to be applied

4. **Debugging:**
   - Always check logs: `docker compose logs -f`
   - Use `docker compose exec <service> bash` to inspect containers
   - Check container status: `docker compose ps`

---

## 🆘 Need Help?

```bash
# Docker Compose help
docker compose --help

# Service-specific logs
docker compose logs backend
docker compose logs frontend
docker compose logs spark-history

# Interactive shell
docker compose exec backend bash
```
