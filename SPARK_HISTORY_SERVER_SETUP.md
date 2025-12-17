# Spark History Server - Proper Infrastructure Setup

## Overview

Implemented a **separate Spark History Server container** to properly manage and persist Spark execution history. This solves the problem of Spark UI being unavailable after code execution completes.

## Architecture

### Before (Problematic)
```
Backend Container
  └── Spark Session (temporary)
      └── Spark UI on port 4040
          ❌ Disappears when session stops
          ❌ Not accessible after execution
```

### After (Proper Solution)
```
Spark History Server Container (Always Running)
  └── Spark History Server on port 18080
      ✅ Persists ALL executions
      ✅ Always accessible
      ✅ View past runs anytime

Backend Container
  └── Spark Session (temporary)
      └── Writes event logs to shared volume
          └── /tmp/spark-events (shared)

Shared Volume (spark-events)
  └── Event logs from all executions
      └── Read by History Server
```

## What Was Created

### 1. Spark History Server Container
**Location:** `/spark-history/`

**Files:**
- `Dockerfile` - Builds container with Spark 3.5.0 and History Server
- `spark-defaults.conf` - Configuration for History Server

**Key Features:**
- Runs independently, always available
- Port: **18080**
- Reads event logs from shared volume
- Retains last 50 applications

### 2. Shared Volume
**Name:** `spark-events`

**Purpose:**
- Backend writes Spark event logs here
- History Server reads event logs from here
- Persists across container restarts

### 3. Updated Backend
**Changes:**
- Enabled event logging in SparkSession
- Writes to `/tmp/spark-events`
- Unique app name per execution (timestamp-based)

### 4. Updated Frontend
**Changes:**
- Button now says "📊 View Spark History"
- Links to http://localhost:18080
- Opens History Server instead of live UI

## Docker Compose Configuration

```yaml
services:
  spark-history:
    build: ./spark-history
    ports:
      - "18080:18080"  # History Server UI
    volumes:
      - spark-events:/tmp/spark-events
    networks:
      - spark-playground-network

  backend:
    volumes:
      - spark-events:/tmp/spark-events  # Shared with history server
    environment:
      - SPARK_EVENT_LOG_DIR=/tmp/spark-events
    depends_on:
      - spark-history

volumes:
  spark-events:  # Shared volume for event logs
```

## How It Works

### Execution Flow:

1. **User Runs Code**
   ```
   User clicks "Run Factory"
   ↓
   Backend creates SparkSession with:
     - Event logging enabled
     - Logs to /tmp/spark-events
     - Unique app name
   ↓
   Code executes
   ↓
   Event log written to shared volume
   ↓
   SparkSession stops
   ```

2. **Viewing History**
   ```
   User clicks "View Spark History"
   ↓
   Opens http://localhost:18080
   ↓
   History Server shows ALL past executions
   ↓
   User can click on any execution to see details
   ```

### What Users See:

**History Server Main Page:**
- List of all Spark applications
- Completion time, duration, user
- Click any app to see details

**Application Details:**
- Jobs, Stages, Tasks
- SQL queries and execution plans
- DAG visualization
- Metrics and timing
- **Everything persists forever!**

## Benefits

### 1. Persistence ✅
- Execution history saved permanently
- View past runs anytime
- Compare different attempts

### 2. Always Available ✅
- History Server runs 24/7
- No need for active Spark session
- Access from anywhere

### 3. Professional Setup ✅
- Same as production Spark clusters
- Proper separation of concerns
- Clean infrastructure

### 4. Educational Value ✅
- See progression over time
- Compare optimizations
- Learn from past mistakes

## Port Mapping

| Service | Internal Port | External Port | URL |
|---------|---------------|---------------|-----|
| Frontend | 5173 | 5173 | http://localhost:5173 |
| Backend API | 8000 | 8000 | http://localhost:8000 |
| Spark History | 18080 | 18080 | http://localhost:18080 |

## Starting the System

```bash
# Build all containers
docker-compose build

# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f spark-history
```

## Verifying It Works

### 1. Check Spark History Server is Running
```bash
docker-compose ps spark-history
# Should show: Up X minutes

curl http://localhost:18080
# Should return HTML
```

### 2. Run Some Code
```bash
# Visit http://localhost:5173
# Click a puzzle
# Click "Run Factory"
# Wait for completion
```

### 3. Check Event Logs Written
```bash
docker-compose exec backend ls -la /tmp/spark-events
# Should see event log files
```

### 4. View in History Server
```bash
# Open http://localhost:18080
# Should see your application listed
# Click on it to see details
```

## Troubleshooting

### History Server Not Starting
```bash
# Check logs
docker-compose logs spark-history

# Common issue: Port already in use
lsof -ti:18080 | xargs kill -9

# Restart
docker-compose restart spark-history
```

### No Applications Showing
```bash
# Check if event logs exist
docker-compose exec spark-history ls -la /tmp/spark-events

# Check if backend can write
docker-compose exec backend ls -la /tmp/spark-events

# Verify permissions
docker-compose exec spark-history chmod -R 777 /tmp/spark-events
```

### Button Shows But Page Doesn't Load
```bash
# Verify History Server is accessible
curl http://localhost:18080

# Check if container is running
docker-compose ps spark-history

# Restart if needed
docker-compose restart spark-history
```

## Event Log Structure

Each execution creates an event log file:
```
/tmp/spark-events/
├── local-1733681234567
├── local-1733681345678
└── local-1733681456789
```

Format: `local-<timestamp>`

Contains:
- All Spark events
- Job submissions
- Stage completions
- Task metrics
- SQL queries
- Shuffle data

## Configuration

### spark-defaults.conf
```properties
# Event log directory
spark.eventLog.dir=file:///tmp/spark-events

# Enable event logging
spark.eventLog.enabled=true

# History Server settings
spark.history.fs.logDirectory=file:///tmp/spark-events
spark.history.ui.port=18080
spark.history.retainedApplications=50
```

### Backend Environment Variables
```yaml
environment:
  - SPARK_EVENT_LOG_DIR=/tmp/spark-events
```

## Comparison: Live UI vs History Server

| Feature | Live Spark UI (4040) | History Server (18080) |
|---------|---------------------|------------------------|
| Availability | Only while running | Always available |
| Persistence | Lost when stopped | Saved forever |
| Past executions | No | Yes, all history |
| Current execution | Real-time | After completion |
| Use case | Debugging live jobs | Reviewing past runs |

## Educational Benefits

### For Students:
1. **Track Progress**: See how solutions improve over time
2. **Compare Attempts**: View different optimization approaches
3. **Learn from Mistakes**: Review failed attempts
4. **Understand Patterns**: See how different operations affect performance

### For Instructors:
1. **Review Student Work**: See all student attempts
2. **Identify Common Issues**: Pattern recognition across students
3. **Demonstrate Concepts**: Show real execution examples
4. **Performance Analysis**: Compare different solutions

## Future Enhancements

### Potential Improvements:
1. **Application Grouping**
   - Group by puzzle
   - Group by user
   - Group by date

2. **Enhanced Filtering**
   - Filter by performance
   - Filter by correctness
   - Filter by optimization used

3. **Comparison Tool**
   - Side-by-side execution comparison
   - Performance diff visualization
   - Optimization suggestions

4. **Integration with UI**
   - Link directly to specific job/stage
   - Embedded History Server view
   - Real-time updates

## Summary

The Spark History Server setup provides:

✅ **Persistent storage** of all Spark executions
✅ **Always-available UI** for viewing history
✅ **Professional infrastructure** matching production setups
✅ **Educational value** through execution tracking
✅ **Clean separation** of concerns
✅ **Proper resource management**

Users can now:
1. Run their code
2. Click "View Spark History"
3. See ALL their past executions
4. Explore detailed metrics anytime
5. Learn from their progression

---

**Status**: ✅ Implementation Complete
**Containers**: 3 (frontend, backend, spark-history)
**Ports**: 5173 (frontend), 8000 (backend), 18080 (history)
**Storage**: Persistent volume for event logs
**URL**: http://localhost:18080
