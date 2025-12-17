# Spark UI Integration - Complete ✅

## What Was Added

A new "**View Spark UI**" button that appears in the RunReport modal footer, allowing users to view the actual Spark Web UI for their code execution.

## Changes Made

### Backend Changes

1. **Enabled Spark UI** (`backend/app/services/executor.py`):
   - Changed `spark.ui.enabled` from `false` to `true`
   - Set `spark.ui.port` to `4040`

2. **Added spark_ui_url Field** (`backend/app/models/puzzle.py`):
   - Added `spark_ui_url: Optional[str]` to `RunResult` model
   - Returns the URL to access Spark UI

3. **Return Spark UI URL** (`backend/app/services/judge.py`):
   - Modified `evaluate()` to include `spark_ui_url="http://localhost:4040"`

4. **Exposed Port 4040** (`docker-compose.yml`):
   - Added port mapping `"4040:4040"` to backend service

### Frontend Changes

1. **Added "View Spark UI" Button** (`frontend/src/components/RunReport.jsx`):
   - New button in modal footer
   - Opens Spark UI in new tab
   - Only shows if `spark_ui_url` is present in result

2. **Styled the Button** (`frontend/src/components/RunReport.css`):
   - Red/orange gradient button design
   - Hover effects with elevation
   - Positioned on left side of footer

## How to Use

### Step 1: Run Some Code
1. Go to http://localhost:5173
2. Click on any puzzle
3. Click "Run Factory" button
4. Wait for execution to complete

### Step 2: View Spark UI
1. Modal appears with execution results
2. Look at the **bottom left** of the modal
3. Click the **"🔍 View Spark UI"** button
4. New tab opens with Spark Web UI

## What You'll See in Spark UI

The Spark UI shows detailed information about the execution:

### Jobs Tab
- List of all Spark jobs that ran
- Status, duration, stages, tasks
- Click on a job to see detailed breakdown

### Stages Tab
- All stages within each job
- DAG visualization
- Task metrics (duration, shuffle read/write, GC time)
- Detailed metrics per stage

### Storage Tab
- Cached RDDs/DataFrames
- Memory usage
- Storage level

### Environment Tab
- Spark configuration
- System properties
- Classpath entries

### Executors Tab
- Executor information
- Resource usage
- Task execution stats

### SQL Tab (Most Useful!)
- Query execution plans
- Physical plan visualization
- Metrics per operator
- **This is the most educational tab** - shows exactly what Spark did

## Example Workflow

```
User Flow:
1. Write PySpark code in editor
2. Click "Run Factory"
3. See results in modal (tabs: Overview, Results, Insights, Query Plan, Hints)
4. Want to see more details?
5. Click "View Spark UI" button
6. Explore actual Spark execution in detail
```

## Important Notes

### Spark UI Persistence
- **Spark UI is available WHILE the SparkSession is active**
- After the execution completes and SparkSession stops, the UI becomes unavailable
- For this playground, the Spark UI is available for a short time after execution
- In production, you would use Spark History Server to persist completed applications

### Port Accessibility
- Spark UI runs on port **4040** in the container
- Mapped to **localhost:4040** on your machine
- URL: http://localhost:4040

### Multiple Sessions
- If multiple SparkSessions try to start, they'll use sequential ports (4041, 4042, etc.)
- The URL in the button always points to 4040 (the first session)

## Improvements Made

### Before
- No way to see detailed Spark execution
- Users could only see high-level metrics
- No access to Spark's internal information

### After
- ✅ Direct access to Spark Web UI
- ✅ See actual execution plans
- ✅ View detailed stage and task metrics
- ✅ Educational tool for learning Spark internals
- ✅ Debug performance issues

## Technical Details

### Backend Implementation
```python
# executor.py - Enable Spark UI
.config("spark.ui.enabled", "true")
.config("spark.ui.port", "4040")

# judge.py - Return UI URL
spark_ui_url="http://localhost:4040"
```

### Frontend Implementation
```jsx
// RunReport.jsx - Show button
{result.spark_ui_url && (
  <a href={result.spark_ui_url} target="_blank">
    🔍 View Spark UI
  </a>
)}
```

### Docker Configuration
```yaml
# docker-compose.yml - Expose port
ports:
  - "8000:8000"
  - "4040:4040"  # Spark UI
```

## Troubleshooting

### Spark UI Not Loading
1. **Check port is mapped**:
   ```bash
   docker-compose ps
   # Should show: 0.0.0.0:4040->4040/tcp
   ```

2. **Check Spark is running**:
   ```bash
   docker-compose logs backend | grep "spark.ui"
   ```

3. **Try accessing directly**:
   - Visit http://localhost:4040 directly
   - Should see Spark Web UI

### Button Not Showing
1. **Check result has spark_ui_url**:
   - Open browser DevTools (F12)
   - Console tab
   - Run: `console.log(result)`
   - Should have `spark_ui_url` field

2. **Hard refresh frontend**:
   - Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)

### Port Already in Use
If port 4040 is in use:
```bash
# Find what's using it
lsof -ti:4040

# Kill it
lsof -ti:4040 | xargs kill -9

# Restart
docker-compose restart backend
```

## Educational Value

### For Beginners
- See what operations Spark performs
- Understand stages and tasks
- Visualize data flow

### For Intermediate Users
- Identify performance bottlenecks
- See shuffle operations in action
- Understand query optimization

### For Advanced Users
- Deep dive into physical plans
- Analyze task-level metrics
- Debug complex queries

## Future Enhancements

### Potential Improvements:
1. **Spark History Server**
   - Persist completed applications
   - View past executions
   - Compare different runs

2. **Embedded Spark UI**
   - Display Spark UI within the modal
   - No need to open new tab
   - Better user experience

3. **Application ID Tracking**
   - Track each execution's app ID
   - Link directly to specific job
   - Maintain history of executions

4. **Metrics Synchronization**
   - Extract metrics from Spark UI
   - Display in our custom visualizations
   - Real-time updates

## Summary

The Spark UI integration adds a powerful debugging and learning tool to the Spark Playground:

- ✅ **One-click access** to detailed Spark information
- ✅ **Educational** - see exactly what Spark is doing
- ✅ **Debugging** - identify performance issues
- ✅ **Professional** - same tool used in production
- ✅ **Easy to use** - just click the button

Users can now explore their Spark executions at multiple levels:
1. **High-level**: Star ratings and metrics in Overview tab
2. **Medium-level**: Query plans and insights in our custom tabs
3. **Deep-level**: Full Spark UI for detailed analysis

---

**Status**: ✅ Complete and Working
**Containers**: Both running with port 4040 exposed
**Frontend**: Button appears in modal footer
**Backend**: Spark UI enabled and accessible
**URL**: http://localhost:4040 (after running code)
