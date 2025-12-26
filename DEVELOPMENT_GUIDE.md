# 🚀 Fast Development Guide

## ⚡ Quick Answer: Use `./dev-restart.sh` for 99% of code changes!

Your setup already has **hot reload** enabled. Most changes don't need a rebuild at all!

---

## 📋 Script Decision Tree

```
Did you change code in .py or .jsx files?
  └─ YES → Use ./dev-restart.sh (3 seconds) ⚡

Did you add/remove Python or Node packages?
  └─ YES → Use ./quick-rebuild.sh (1-2 minutes) 🚀

Is something broken and you want a fresh start?
  └─ YES → Use ./full-rebuild.sh (5+ minutes) 🔨

Starting for the first time today?
  └─ YES → Use ./start.sh (10 seconds) ✨
```

---

## 🎯 Scripts Ranked by Speed

| Script | Speed | Use When | Rebuilds? |
|--------|-------|----------|-----------|
| `./dev-restart.sh` | ⚡ **3 sec** | Changed .py/.jsx/.css files | ❌ No |
| `./start.sh` | ✨ **10 sec** | Starting containers | ❌ No |
| `./stop.sh` | 🛑 **2 sec** | Stopping containers | ❌ No |
| `./quick-rebuild.sh` | 🚀 **1-2 min** | Added packages | ✅ Yes (cached) |
| `./restart.sh` | 📦 **1-2 min** | General rebuild | ✅ Yes (cached) |
| `./full-rebuild.sh` | 🔨 **5+ min** | Something's broken | ✅ Yes (no cache) |

---

## ⚡ Fast Development Workflow

### Daily Usage (FASTEST)

```bash
# Morning - Start once
./start.sh

# Edit code all day - NO NEED TO RESTART!
# Frontend auto-reloads (Vite HMR)
# Backend auto-reloads (Uvicorn --reload)

# Only if hot reload isn't working
./dev-restart.sh  # Takes 3 seconds

# Evening - Stop
./stop.sh
```

### Why Is This Fast?

1. **Volume Mounts** - Your code is mounted into containers:
   ```yaml
   volumes:
     - ./backend/app:/app/app     # Backend code
     - ./frontend:/app            # Frontend code
   ```

2. **Hot Reload Enabled**:
   - **Backend**: Uvicorn with `--reload` flag watches for .py changes
   - **Frontend**: Vite dev server with HMR (Hot Module Replacement)

3. **No Rebuild Needed** - Changes appear instantly without rebuilding images!

---

## 🔄 When Hot Reload Works

### ✅ NO REBUILD NEEDED for:

**Backend:**
- ✅ Changing `.py` files
- ✅ Modifying API endpoints
- ✅ Updating models, services
- ✅ Fixing bugs in Python code

**Frontend:**
- ✅ Changing `.jsx/.tsx` files
- ✅ Updating CSS/styles
- ✅ Modifying components
- ✅ Changing UI logic

**Action:** Just save the file! Changes appear in 1-2 seconds.

### ⚠️ RESTART NEEDED for:

**Use `./dev-restart.sh` (3 seconds):**
- ⚠️ Hot reload stopped working
- ⚠️ Environment variable changes
- ⚠️ Container configuration tweaks

**Use `./quick-rebuild.sh` (1-2 minutes):**
- 📦 Added Python package to `pyproject.toml`
- 📦 Added Node package to `package.json`
- 📦 Changed Dockerfile
- 📦 Changed base image

**Use `./full-rebuild.sh` (5+ minutes):**
- 🔨 Something is completely broken
- 🔨 Docker cache is corrupted
- 🔨 Mysterious errors that won't go away

---

## 🎬 Real Examples

### Example 1: Fixing a Bug in Backend

```bash
# 1. Start containers (once per day)
./start.sh

# 2. Edit backend/app/services/execution_simulator.py
#    Fix bug in partition lineage calculation
#    → SAVE FILE

# 3. Check browser/API - change appears automatically!
#    No restart needed! Uvicorn detected change and reloaded.
```

### Example 2: Adding a New React Component

```bash
# 1. Containers already running
#    (If not: ./start.sh)

# 2. Create frontend/src/components/NewComponent.jsx
#    → SAVE FILE

# 3. Import it in another component
#    → SAVE FILE

# 4. Check browser - component appears instantly!
#    Vite HMR updated the page automatically.
```

### Example 3: Adding a New Python Package

```bash
# 1. Edit backend/pyproject.toml
#    Add: pandas = "^2.0.0"

# 2. Rebuild WITH cache (reuses existing layers)
./quick-rebuild.sh  # Takes 1-2 minutes

# 3. Import and use pandas in your code
#    → Changes auto-reload from here on
```

### Example 4: Adding a New React Package

```bash
# Option A: Rebuild (recommended)
# 1. Edit frontend/package.json
#    Add: "axios": "^1.6.0"
# 2. Rebuild
./quick-rebuild.sh

# Option B: Install in running container (faster)
docker compose exec frontend npm install axios
# Then use it in code - auto-reloads!
```

---

## 🐛 Troubleshooting

### Hot Reload Not Working?

```bash
# Quick fix - restart containers (3 seconds)
./dev-restart.sh

# Check logs to see if there's an error
docker compose logs -f backend
docker compose logs -f frontend

# If still not working - rebuild
./quick-rebuild.sh
```

### "Module Not Found" Error?

```bash
# You probably added a new package
# Rebuild to install it:
./quick-rebuild.sh
```

### Port Already in Use?

```bash
# Something else is using the port
# Option 1: Stop that other process
lsof -i :5173  # Frontend
lsof -i :8000  # Backend

# Option 2: Change ports in docker-compose.yml
```

### Everything is Broken?

```bash
# Nuclear option - fresh start
./full-rebuild.sh

# Or even more nuclear
docker compose down -v
docker system prune -a
./full-rebuild.sh
```

---

## 📊 Performance Comparison

### Scenario: Fixing a bug in Python code

| Method | Time | Steps |
|--------|------|-------|
| ✅ **Hot Reload** | **1-2 sec** | Just save file |
| ⚡ `./dev-restart.sh` | 3 sec | Restart containers |
| 🚀 `./quick-rebuild.sh` | 90 sec | Rebuild with cache |
| 🔨 `./full-rebuild.sh` | 300+ sec | Rebuild from scratch |

**Speedup:** Hot reload is **150x faster** than full rebuild! 🚀

---

## 💡 Pro Tips

1. **Keep Containers Running**
   - Don't stop containers between code changes
   - Let hot reload do its magic
   - Only stop at end of day

2. **Watch the Logs**
   ```bash
   # Terminal 1: Your editor
   # Terminal 2: Backend logs
   docker compose logs -f backend
   # Terminal 3: Frontend logs
   docker compose logs -f frontend
   ```
   You'll see when files are reloaded!

3. **Rebuild vs Restart**
   - **Restart** = stop and start containers (fast, 3 sec)
   - **Rebuild** = rebuild images then start (slow, 1-5 min)
   - Most changes need **neither** (hot reload)!

4. **Cache is Your Friend**
   - Docker caches each layer
   - `./quick-rebuild.sh` reuses cached layers
   - Only rebuilds changed parts
   - **Never use** `./full-rebuild.sh` in development!

5. **Verify Hot Reload is Working**
   ```bash
   # Add a console.log or print statement
   # Save file
   # Check logs - should see reload message
   docker compose logs backend | grep -i reload
   ```

---

## 🎯 Summary

### For 99% of Development

```bash
# Start once
./start.sh

# Code all day - changes auto-reload
# (no need to run anything)

# Only if hot reload breaks
./dev-restart.sh
```

### When Adding Packages

```bash
# Edit package.json or pyproject.toml
./quick-rebuild.sh
```

### When Everything is Broken

```bash
# Last resort
./full-rebuild.sh
```

---

## 📚 More Info

- See `DOCKER_SCRIPTS_README.md` for detailed Docker commands
- Check `docker-compose.yml` to see volume mounts
- View Dockerfiles to see hot reload configuration

---

**🎉 Enjoy lightning-fast development with hot reload!**
