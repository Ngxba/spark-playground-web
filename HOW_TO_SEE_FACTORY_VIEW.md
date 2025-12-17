# How to See the New Factory View

## IMPORTANT: Location

The **new Factory View** I just implemented is NOT in the puzzle description area.

It appears in the **Run Report modal** after you execute code.

## Step-by-Step Guide

### 1. Start the Application

```bash
# Make sure Docker containers are running
docker-compose ps

# If not running:
docker-compose up -d
```

### 2. Open the Application

Visit: **http://localhost:5173**

### 3. Select a Puzzle

Click any puzzle card (e.g., "Group the Fruits")

### 4. Write or Use Starter Code

The code editor will have some starter code. You can:
- Use the existing code
- OR write your own solution

Example code for "Group the Fruits":
```python
result = fruits.sort_values('type')
```

### 5. Run the Code

Click the **"▶ Run Code"** button (or similar)

Wait 2-3 seconds for execution...

### 6. Run Report Modal Opens

A large modal window will appear with:
- Header showing "Run Report"
- Status badge (✅ Correct or ❌ Incorrect)
- **6 TABS at the top**

### 7. Click the "Factory View" Tab

The tabs are:
1. Overview
2. **← Factory View** ⭐ **CLICK THIS ONE!**
3. Results
4. Insights
5. Query Plan
6. Hints

### 8. See the New Factory View!

You should now see:

#### Top Section: Timeline Controls
```
⏮ ▶ ⏸    Speed: [0.5x] [1x] [2x] [4x]    Time: 0.00s / 5.20s
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### Middle Section: Cluster View
```
🖥️ Cluster: 4 Worker Nodes

┌─ Worker 1 ──┐  ┌─ Worker 2 ──┐  ┌─ Worker 3 ──┐  ┌─ Worker 4 ──┐
│ [🟣][🟣]    │  │ [🟣][🟣]    │  │ [🟣][🟣]    │  │ [🟣][🟣]    │
│ [⚫][⚫]    │  │ [⚫][⚫]    │  │ [⚫][⚫]    │  │ [⚫][⚫]    │
│ 2/4 cores   │  │ 2/4 cores   │  │ 2/4 cores   │  │ 2/4 cores   │
└─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘

🟣 = Active core (pulsing animation)
⚫ = Idle core
```

#### Middle Section: Stage Flow
```
🏭 Execution Pipeline: 2 Stages

┌─────────────┐        ┌─────────────┐
│ 📁 Scan     │   →    │ 🔀 Shuffle  │
│ Stage 0     │   →    │ 15.3 MB     │
│ ████████░░  │   →    │ ████████░░  │
└─────────────┘        └─────────────┘
  10 tasks                10 tasks
```

#### Bottom Section: Live Metrics
```
⚡ Active Tasks: 8        🔢 Partitions: 10
✓ Completed: 12/20       🏭 Total Stages: 2
```

#### Bottom Section: Educational Concepts
```
💡 Learn Spark Concepts

[+] 🔢 Partitions - Data is split into chunks...
[+] 🏭 Stages - Execution is broken into phases...
[+] 🔀 Shuffles - Expensive data movement...
```

### 9. Press Play!

Click the **▶ Play** button in the timeline controls

Watch the animation:
- CPU cores light up as tasks run
- Stage progress bars fill up
- Metrics update in real-time
- Timeline scrubber moves forward

### 10. Experiment!

Try:
- Adjusting playback speed (0.5x, 1x, 2x, 4x)
- Pausing and seeking through the timeline
- Hovering over elements for tooltips
- Expanding educational concepts
- Running different puzzles to see different patterns

## What Each Puzzle Shows

### Group Fruits (Easy)
- Simple scan + sort
- 1-2 stages
- Minimal shuffles
- Good for learning basics

### Fast Join (Medium)
- Join operation
- Shows shuffle vs broadcast difference
- 2-3 stages
- Great for understanding join strategies

### Cache Puzzle (Hard)
- Multiple operations on same data
- Shows benefit of caching
- 3+ stages
- Demonstrates recomputation

## Troubleshooting

### I don't see the "Factory View" tab

**Solution**: Make sure you rebuilt the Docker containers:
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

Then hard refresh your browser:
- **Mac**: Cmd + Shift + R
- **Windows/Linux**: Ctrl + Shift + R

### The tab is there but shows "No Execution Simulation Available"

**Possible causes**:
1. Code execution failed before generating simulation
2. Backend error preventing simulation generation

**Solution**: Check backend logs:
```bash
docker-compose logs backend --tail=100
```

### Animation doesn't play

**Solutions**:
1. Check browser console for JavaScript errors (F12)
2. Try a different browser
3. Clear browser cache and reload

### Performance is laggy

**Solutions**:
1. Close other browser tabs
2. Try slower playback speed (0.5x)
3. Use Chrome or Firefox for best performance

## What You Should See When It Works

### Before Pressing Play
- Timeline at 0.00s
- All cores idle (gray)
- All stages pending
- Metrics showing 0 active tasks

### During Playback
- Timeline advancing smoothly
- CPU cores lighting up (purple/gradient)
- Cores pulsing with animation
- Stage progress bars filling
- Metrics updating (8 active, 12 completed, etc.)
- Current stage indicator highlighting

### After Completion
- Timeline at end (e.g., 5.20s)
- All cores idle again
- All stages completed (green)
- All tasks completed (20/20)

## Expected Behavior

### Simple Queries (1 stage)
- ~2-3 second animation
- 10 tasks run in parallel
- All stages complete quickly

### Complex Queries (2+ stages)
- ~5-8 second animation
- Multiple stages run sequentially
- Shuffle operations visible between stages
- More tasks overall

### Broadcast Joins
- No shuffle between stages!
- Faster execution
- Less data movement

## Comparison: Old vs New

### OLD Factory View (Still exists in puzzle description)
- Static SVG animation
- Generic boxes moving on conveyor belts
- No real execution data
- Simple placeholder

### NEW Factory View (In Run Report modal)
- Real execution simulation from Spark plans
- Actual stages, tasks, and nodes
- Timeline controls with playback
- Educational tooltips
- Live metrics
- Based on your actual code execution

## Architecture

```
User writes code
       ↓
Click "Run Code"
       ↓
Backend executes with PySpark
       ↓
Captures physical plan
       ↓
ExecutionSimulator generates simulation
       ↓
API returns RunResult with execution_simulation
       ↓
Frontend receives data
       ↓
Run Report modal opens
       ↓
User clicks "Factory View" tab
       ↓
FactoryView component loads
       ↓
Animation plays when user clicks Play
       ↓
60fps animation showing real execution!
```

## Example Workflow

```bash
# 1. Start Docker
docker-compose up -d

# 2. Open browser
open http://localhost:5173

# 3. Click "Group the Fruits" puzzle

# 4. In code editor, paste:
result = fruits.groupby('type').apply(lambda x: x).reset_index(drop=True)

# 5. Click "Run Code"

# 6. Wait for modal to appear

# 7. Click "Factory View" tab (2nd tab)

# 8. Click Play button (▶)

# 9. Watch:
   - Scan stage processes 10 partitions
   - Tasks assigned to 4 nodes
   - 16 cores running in parallel
   - GroupBy operation
   - Shuffle moving data
   - Final aggregation

# 10. Try different speed (2x, 4x)

# 11. Expand "Partitions" concept to learn more

# 12. Click "Insights" tab to see optimization suggestions

# 13. Close modal, modify code, run again!
```

---

**Status**: ✅ Factory View Implementation Complete
**Location**: Run Report Modal → "Factory View" Tab
**Requirements**: Docker containers rebuilt with new code
**Browser**: Chrome, Firefox, Safari, Edge (all supported)
