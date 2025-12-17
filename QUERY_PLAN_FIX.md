# Query Plan Visualization Fix

## Problem

The Query Plan tab in the Run Report was completely broken - users couldn't see:
- Visual DAG
- Physical Plan
- Logical Plan

This is a critical learning feature to help students understand how Spark executes their queries.

## Root Cause

The backend was only returning `dag_structure` (nodes and edges for the visual DAG), but NOT the raw text of the physical and logical plans. The QueryPlanViewer component was looking for these plans inside `dagStructure.physical_plan` and `dagStructure.logical_plan`, which didn't exist.

## Solution

### 1. Backend - Added Plan Fields to Model

**File:** `/backend/app/models/puzzle.py`

Added two new fields to `RunResult`:

```python
physical_plan: Optional[str] = Field(default=None, description="Spark physical execution plan")
logical_plan: Optional[str] = Field(default=None, description="Spark logical query plan")
```

### 2. Backend - Return Plans in Judge

**File:** `/backend/app/services/judge.py`

Modified judge to extract and return the raw plans:

```python
# Include DAG structure and query plans for frontend visualization
dag_structure = None
physical_plan = None
logical_plan = None

if execution_metadata and 'physical_plan' in execution_metadata:
    dag_structure = self.operation_detector.extract_dag_structure(
        execution_metadata['physical_plan']
    )
    # Include raw plans for Query Plan viewer
    physical_plan = execution_metadata.get('physical_plan')
    logical_plan = execution_metadata.get('logical_plan')

return RunResult(
    # ...
    dag_structure=dag_structure,  # DAG structure for Visual DAG tab
    physical_plan=physical_plan,  # Raw physical plan for Physical Plan tab
    logical_plan=logical_plan,    # Raw logical plan for Logical Plan tab
    # ...
)
```

### 3. Frontend - Update RunReport to Pass Plans

**File:** `/frontend/src/components/RunReport.jsx`

Updated to pass all three pieces of data:

```jsx
{activeTab === 'query-plan' && (
  <QueryPlanViewer
    dagStructure={result.dag_structure}
    physicalPlan={result.physical_plan}
    logicalPlan={result.logical_plan}
  />
)}
```

### 4. Frontend - Update QueryPlanViewer Component

**File:** `/frontend/src/components/QueryPlanViewer.jsx`

Updated to accept and use the separate props:

```jsx
function QueryPlanViewer({ dagStructure, physicalPlan, logicalPlan }) {
  // Check if we have any data to display
  const hasVisualData = dagStructure && dagStructure.nodes && dagStructure.edges;
  const hasPhysicalPlan = physicalPlan && physicalPlan.trim().length > 0;
  const hasLogicalPlan = logicalPlan && logicalPlan.trim().length > 0;

  // ... render logic using these flags

  {activeView === 'physical' && (
    <pre className="plan-content">
      {hasPhysicalPlan ? formatPlan(physicalPlan) : 'No physical plan available'}
    </pre>
  )}

  {activeView === 'logical' && (
    <pre className="plan-content">
      {hasLogicalPlan ? formatPlan(logicalPlan) : 'No logical plan available'}
    </pre>
  )}
}
```

## What Each Tab Shows

### Visual DAG Tab
- Interactive node-based visualization using ReactFlow
- Color-coded operations (Broadcast, Shuffle, Filter, etc.)
- Shows data flow through the query plan
- **Educational value**: Visual representation helps students see the execution flow

### Physical Plan Tab
- Raw Spark physical execution plan
- Syntax-highlighted operations
- Legend showing operation types and costs
- **Educational value**: Shows exactly how Spark will execute, including shuffle costs

### Logical Plan Tab
- Raw Spark logical query plan
- Shows the high-level query structure before optimization
- **Educational value**: Helps students understand query optimization - compare logical vs physical to see what Spark optimized

## Educational Benefits

This fix restores critical learning tools:

1. **Visual Learning**: DAG visualization for visual learners
2. **Deep Understanding**: Compare logical vs physical plans to learn optimization
3. **Performance Awareness**: See which operations cause shuffles (expensive)
4. **Real Spark Knowledge**: Same plans they'll see in production Spark UIs

## Status

**Backend changes**: Complete, needs container rebuild
**Frontend changes**: Complete, auto-reloaded by Vite dev server

## Testing

After backend rebuild, test by:

1. Run any puzzle
2. Click "Query Plan" tab
3. Verify all 3 sub-tabs work:
   - Visual DAG: Shows interactive graph
   - Physical Plan: Shows highlighted text plan
   - Logical Plan: Shows logical query structure

## Next Steps

Backend container needs to be rebuilt to pick up the model and judge changes:

```bash
docker-compose build backend
docker-compose up -d backend
```

Then test all three tabs to ensure visualization works properly.
