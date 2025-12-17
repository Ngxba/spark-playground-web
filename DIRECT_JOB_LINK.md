# Direct Link to Specific Spark Job

## Problem

You correctly identified that users clicking "View Spark History" were taken to the History Server homepage showing ALL applications, not the specific job they just ran. This is confusing UX - users want to see THEIR job immediately.

## Solution

Modified the system to link directly to the specific application details page instead of the generic history homepage.

### Changes Made

#### 1. Backend - Capture Application ID (`executor.py`)

Added code to capture the Spark Application ID when creating the SparkSession:

```python
# Capture application ID for History Server link
app_id = spark.sparkContext.applicationId
```

Then added it to the execution metadata:

```python
# Add application ID to metadata
if execution_metadata and app_id:
    execution_metadata['app_id'] = app_id
```

#### 2. Backend - Build Specific URL (`judge.py`)

Modified the judge to construct a direct link to the specific application:

```python
# Build specific application URL if we have app_id
spark_ui_url = "http://localhost:18080"
if execution_metadata and 'app_id' in execution_metadata:
    app_id = execution_metadata['app_id']
    # Link directly to the specific application details page
    spark_ui_url = f"http://localhost:18080/history/{app_id}/jobs/"
```

#### 3. Frontend - Updated Button Text (`RunReport.jsx`)

Changed button text to be more specific:

```jsx
📊 View This Job in Spark UI
```

(Previously: "📊 View Spark History")

## How It Works Now

### Before
1. User runs code
2. Clicks button
3. Goes to `http://localhost:18080` (homepage with ALL apps)
4. User has to find their specific execution in the list
5. Click again to see details

### After
1. User runs code
2. Clicks button
3. Goes directly to `http://localhost:18080/history/local-1765239951154/jobs/`
4. Immediately sees THEIR specific job's details

## URL Format

The Spark History Server uses this URL pattern:
```
http://localhost:18080/history/{applicationId}/jobs/
```

Where `applicationId` looks like: `local-1765239951154`

## Benefits

✅ **Immediate Context**: Users see their specific job right away
✅ **No Search Required**: Don't need to hunt through list of all applications
✅ **Better UX**: One click to relevant information
✅ **Clear Intent**: Button text "View This Job" makes it obvious

## Status

Currently rebuilding backend container to include these changes. Once complete, the button will link directly to the specific Spark job that was just executed.

## Testing

After rebuild completes, test with:

```bash
# Run a job
curl -X POST http://localhost:8000/api/puzzles/group_fruits/run \
  -H "Content-Type: application/json" \
  -d '{"code":"result = fruits.groupBy(\"type\").count()\nresult.show()"}'

# Check the returned URL includes app ID
# Should return something like:
# "spark_ui_url": "http://localhost:18080/history/local-1765239951154/jobs/"
```
