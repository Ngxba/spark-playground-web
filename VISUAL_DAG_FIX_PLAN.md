# Visual DAG Fix Plan

## Problem Statement

The Visual DAG in the Query Plan tab of the Run Report modal is not displaying anything. Users click on "Visual DAG" but see either:
- Empty/blank screen
- "No DAG data available" message
- Components not rendering

---

## Root Cause Analysis

### Potential Issues

1. **Backend - DAG Structure Generation**
   - `extract_dag_structure()` in `operation_detector.py` might not be creating proper nodes/edges
   - Physical plan parsing might be failing
   - Node/edge format might be incorrect
   - Empty or None values being returned

2. **Backend - Data Flow**
   - DAG structure not being included in API response
   - Judge not calling `extract_dag_structure()` correctly
   - Physical plan might be empty/None

3. **Frontend - Data Validation**
   - `dagStructure` prop might be undefined/null
   - Checking `dagStructure.nodes && dagStructure.edges` might fail if structure is different
   - ReactFlow expecting different node/edge format

4. **Frontend - Component Rendering**
   - ReactFlow not initialized properly
   - CSS height/width issues preventing display
   - Node positioning calculations might place nodes off-screen

---

## Diagnostic Steps

### Step 1: Verify Backend is Generating DAG Structure

**Check**: Does `judge.py` call `extract_dag_structure()`?

**File**: `backend/app/services/judge.py` (lines 74-84)

**Current Code**:
```python
dag_structure = None
physical_plan = None
logical_plan = None

if execution_metadata and 'physical_plan' in execution_metadata:
    dag_structure = self.operation_detector.extract_dag_structure(
        execution_metadata['physical_plan']
    )
    physical_plan = execution_metadata.get('physical_plan')
    logical_plan = execution_metadata.get('logical_plan')
```

**Verify**:
- ✅ Code exists and calls `extract_dag_structure()`
- ❓ Check if `physical_plan` has content
- ❓ Check if `dag_structure` is being created

### Step 2: Check Physical Plan Content

**Issue**: Physical plan might be empty or malformed

**Test**:
```python
print("Physical Plan:")
print(physical_plan)
print("\nDAG Structure:")
print(dag_structure)
```

**Expected**:
```
Physical Plan:
*(1) Project [...]
+- *(1) Filter [...]
   +- *(1) Scan [...]

DAG Structure:
{
  'nodes': [
    {'id': 0, 'operation': 'Project', 'depth': 0, 'label': 'Project'},
    {'id': 1, 'operation': 'Filter', 'depth': 1, 'label': 'Filter'},
    {'id': 2, 'operation': 'Scan', 'depth': 2, 'label': 'Scan'}
  ],
  'edges': [
    {'from': 0, 'to': 1},
    {'from': 1, 'to': 2}
  ]
}
```

### Step 3: Verify Frontend Receives Data

**Check**: Does `QueryPlanViewer` receive `dagStructure`?

**Test**: Add console.log in `QueryPlanViewer.jsx`:
```javascript
console.log('DAG Structure:', dagStructure);
console.log('Has nodes?', dagStructure?.nodes);
console.log('Has edges?', dagStructure?.edges);
```

### Step 4: Check ReactFlow Rendering

**Issue**: ReactFlow container might have zero height

**Test**: Check CSS for `.dag-visualization-container`

---

## Fix Implementation Plan

### Phase 1: Backend Fixes

#### Fix 1.1: Improve Physical Plan Parsing
**File**: `backend/app/services/operation_detector.py`

**Problem**: Current parser might not handle all Spark plan formats

**Solution**: Enhance `extract_dag_structure()` to:
- Handle different indentation formats (spaces, tabs, mixed)
- Extract operation details (not just names)
- Handle multi-line operations
- Add fallback for simple operations

**Code Changes**:
```python
@staticmethod
def extract_dag_structure(physical_plan: str) -> Dict[str, any]:
    """
    Extract DAG structure from physical plan for visualization.
    Enhanced to handle various Spark plan formats.
    """
    if not physical_plan or not physical_plan.strip():
        return {'nodes': [], 'edges': []}

    nodes = []
    edges = []
    node_id = 0

    # Parse physical plan line by line
    lines = physical_plan.split('\n')
    node_stack = []
    prev_depth = -1

    for line in lines:
        if not line.strip():
            continue

        # Calculate indentation depth
        stripped = line.lstrip()
        indent_chars = len(line) - len(stripped)

        # Normalize indentation (every 2-3 spaces = 1 level)
        depth = indent_chars // 3

        # Extract operation name (remove prefixes like *(1), +-, etc.)
        operation_line = stripped.lstrip('+*-() ').strip()

        if not operation_line:
            continue

        # Extract operation name before parentheses or brackets
        operation = operation_line.split('(')[0].split('[')[0].strip()

        # Extract details from parentheses/brackets
        details = None
        if '(' in operation_line:
            details_start = operation_line.find('(')
            details_end = operation_line.find(')', details_start)
            if details_end > details_start:
                details = operation_line[details_start+1:details_end]
        elif '[' in operation_line:
            details_start = operation_line.find('[')
            details_end = operation_line.find(']', details_start)
            if details_end > details_start:
                details = operation_line[details_start+1:details_end]

        # Create node
        node = {
            'id': node_id,
            'operation': operation,
            'details': details[:50] if details else None,  # Limit details length
            'depth': depth,
            'label': operation
        }
        nodes.append(node)

        # Create edge from parent based on depth
        if depth > 0 and node_stack:
            # Find parent at previous depth level
            for i in range(len(node_stack) - 1, -1, -1):
                if node_stack[i]['depth'] < depth:
                    parent = node_stack[i]
                    edges.append({
                        'from': parent['id'],
                        'to': node_id
                    })
                    break

            # Clean stack of nodes at same or deeper depth
            node_stack = [n for n in node_stack if n['depth'] < depth]

        # Add current node to stack
        node_stack.append({'id': node_id, 'depth': depth})
        node_id += 1
        prev_depth = depth

    # If we have nodes but no edges, create linear flow
    if len(nodes) > 1 and len(edges) == 0:
        for i in range(len(nodes) - 1):
            edges.append({
                'from': nodes[i]['id'],
                'to': nodes[i + 1]['id']
            })

    return {
        'nodes': nodes,
        'edges': edges
    }
```

#### Fix 1.2: Add Fallback DAG Generation
**File**: `backend/app/services/operation_detector.py`

**Problem**: If plan parsing fails, we should generate simple DAG from operations

**Solution**: Add fallback method:
```python
@staticmethod
def create_simple_dag_from_operations(operations: List[str]) -> Dict[str, any]:
    """
    Create a simple linear DAG when physical plan parsing fails.
    """
    if not operations:
        return {'nodes': [], 'edges': []}

    nodes = []
    edges = []

    for i, op in enumerate(operations):
        nodes.append({
            'id': i,
            'operation': op.capitalize(),
            'details': None,
            'depth': i,
            'label': op.capitalize()
        })

        if i > 0:
            edges.append({
                'from': i - 1,
                'to': i
            })

    return {
        'nodes': nodes,
        'edges': edges
    }
```

#### Fix 1.3: Update Judge to Use Fallback
**File**: `backend/app/services/judge.py`

**Enhancement**: Try extraction, fall back to simple DAG

**Code Change**:
```python
# Include DAG structure and query plans for frontend visualization
dag_structure = None
physical_plan = None
logical_plan = None

if execution_metadata and 'physical_plan' in execution_metadata:
    physical_plan = execution_metadata.get('physical_plan')
    logical_plan = execution_metadata.get('logical_plan')

    # Try to extract DAG from physical plan
    dag_structure = self.operation_detector.extract_dag_structure(physical_plan)

    # If extraction failed, create simple DAG from operations
    if not dag_structure or not dag_structure.get('nodes'):
        operations = analysis.get('operations', [])
        dag_structure = self.operation_detector.create_simple_dag_from_operations(operations)
```

#### Fix 1.4: Add Logging for Debugging
**File**: `backend/app/services/judge.py`

**Add Debug Logging**:
```python
# After generating dag_structure
if dag_structure:
    print(f"Generated DAG: {len(dag_structure.get('nodes', []))} nodes, {len(dag_structure.get('edges', []))} edges")
else:
    print("Warning: No DAG structure generated")
```

---

### Phase 2: Frontend Fixes

#### Fix 2.1: Add Defensive Checks in QueryPlanViewer
**File**: `frontend/src/components/QueryPlanViewer.jsx`

**Problem**: Checking might fail if dagStructure is malformed

**Solution**: More robust validation

**Code Change**:
```javascript
// Line 9-11
const hasVisualData = dagStructure &&
                      Array.isArray(dagStructure.nodes) &&
                      dagStructure.nodes.length > 0 &&
                      Array.isArray(dagStructure.edges);
```

#### Fix 2.2: Add Debug Console Logs
**File**: `frontend/src/components/QueryPlanViewer.jsx`

**Add at top of component**:
```javascript
// Debug logging
useEffect(() => {
  console.log('QueryPlanViewer - dagStructure:', dagStructure);
  console.log('QueryPlanViewer - hasVisualData:', hasVisualData);
  console.log('QueryPlanViewer - nodes:', dagStructure?.nodes);
  console.log('QueryPlanViewer - edges:', dagStructure?.edges);
}, [dagStructure]);
```

#### Fix 2.3: Improve Empty State in DAGVisualization
**File**: `frontend/src/components/DAGVisualization.jsx`

**Enhancement**: Better empty state and debug info

**Code Change**:
```javascript
if (!nodes || nodes.length === 0) {
  console.warn('DAGVisualization: No nodes provided', { nodes, edges });
  return (
    <div className="dag-empty">
      <div className="empty-icon">📊</div>
      <p><strong>No DAG data available</strong></p>
      <p className="empty-hint">
        The query execution plan doesn't contain enough information to visualize.
        Try running a more complex query (e.g., with joins or aggregations).
      </p>
      <details>
        <summary>Debug Info</summary>
        <pre>{JSON.stringify({ nodes, edges }, null, 2)}</pre>
      </details>
    </div>
  );
}
```

#### Fix 2.4: Fix Container Height Issue
**File**: `frontend/src/components/DAGVisualization.css`

**Problem**: Container might have 0 height

**Solution**: Ensure minimum height

**Code Addition**:
```css
.dag-visualization-container {
  width: 100%;
  min-height: 500px;
  height: 100%;
  background: #f9fafb;
  border-radius: 8px;
  overflow: hidden;
}

.visual-dag {
  height: 600px;
  min-height: 600px;
}

.dag-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  padding: 40px;
  text-align: center;
  color: #6b7280;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-hint {
  font-size: 14px;
  color: #9ca3af;
  max-width: 400px;
  margin-top: 8px;
}

details {
  margin-top: 20px;
  padding: 12px;
  background: #f3f4f6;
  border-radius: 6px;
  max-width: 600px;
}

details pre {
  text-align: left;
  font-size: 11px;
  overflow-x: auto;
  max-height: 300px;
}
```

#### Fix 2.5: Improve Node Positioning Algorithm
**File**: `frontend/src/components/DAGVisualization.jsx`

**Problem**: Nodes might be positioned off-screen or overlapping

**Solution**: Better auto-layout

**Code Change**:
```javascript
// Convert nodes to ReactFlow format
const convertedNodes = nodes.map((node, index) => {
  const depth = node.depth || 0;

  // Calculate position with better spacing
  const x = 50 + (index % 4) * 250;  // 4 columns max
  const y = 50 + depth * 120;  // More vertical space

  return {
    id: String(node.id),
    type: 'operation',
    position: { x, y },
    data: {
      operation: node.operation || 'Unknown',
      details: node.details || '',
    },
  };
});
```

---

### Phase 3: Enhanced Error Handling

#### Enhancement 3.1: Add Error Boundary
**File**: `frontend/src/components/QueryPlanViewer.jsx`

**Add try-catch around DAGVisualization**:
```javascript
{activeView === 'visual' && (
  <div className="visual-dag">
    {hasVisualData ? (
      <ErrorBoundary fallback={<div>Error loading DAG visualization</div>}>
        <DAGVisualization
          nodes={dagStructure.nodes}
          edges={dagStructure.edges}
        />
      </ErrorBoundary>
    ) : (
      <div className="no-data-detailed">
        <p>Visual DAG not available</p>
        <p className="hint">Physical plan data: {physicalPlan ? 'Available' : 'Missing'}</p>
        <p className="hint">DAG Structure: {JSON.stringify(dagStructure)}</p>
      </div>
    )}
  </div>
)}
```

#### Enhancement 3.2: Add API Response Validation
**File**: `frontend/src/services/api.js`

**Validate response structure**:
```javascript
const runPuzzle = async (puzzleId, code) => {
  const response = await fetch(`${API_BASE}/puzzles/${puzzleId}/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code }),
  });

  const result = await response.json();

  // Validate dag_structure
  if (result.dag_structure && !Array.isArray(result.dag_structure.nodes)) {
    console.warn('Invalid DAG structure format:', result.dag_structure);
    result.dag_structure = { nodes: [], edges: [] };
  }

  return result;
};
```

---

## Testing Plan

### Test 1: Simple Query (1-2 operations)
**Query**:
```python
result = fruits.sort_values('type')
```

**Expected DAG**:
- 1-2 nodes: Scan, Sort
- 1 edge connecting them

### Test 2: GroupBy Query (Multiple stages)
**Query**:
```python
result = fruits.groupby('type').size().reset_index(name='count')
```

**Expected DAG**:
- 3-4 nodes: Scan, Project, Aggregate, Project
- 3 edges connecting them sequentially

### Test 3: Join Query (With shuffle)
**Query**:
```python
result = orders.merge(cities, on='city_code')
```

**Expected DAG**:
- 5+ nodes: Scan (x2), Exchange (shuffle), Join, Project
- Multiple edges showing data flow

### Test 4: Broadcast Join (Optimized)
**Query**:
```python
result = orders.merge(broadcast(cities), on='city_code')
```

**Expected DAG**:
- 4+ nodes: Scan (x2), BroadcastExchange, BroadcastHashJoin
- Edges showing broadcast pattern

---

## Success Criteria

### Backend Success:
✅ `extract_dag_structure()` returns nodes and edges for all query types
✅ Nodes have `id`, `operation`, `depth`, `label` fields
✅ Edges have `from`, `to` fields
✅ Empty queries return `{'nodes': [], 'edges': []}` instead of `None`
✅ Fallback DAG generation works when parsing fails

### Frontend Success:
✅ Visual DAG displays for all query types
✅ Nodes are visible and properly positioned
✅ Edges connect nodes correctly
✅ Pan, zoom, drag controls work
✅ MiniMap shows overview
✅ Empty state shows helpful message
✅ No console errors

---

## Implementation Order

### Priority 1 (Critical - Do First):
1. ✅ Fix `extract_dag_structure()` parsing (Fix 1.1)
2. ✅ Add fallback DAG generation (Fix 1.2, 1.3)
3. ✅ Add defensive checks in frontend (Fix 2.1)
4. ✅ Fix container height (Fix 2.4)

### Priority 2 (High - Do Next):
5. ✅ Add debug logging (Fix 1.4, 2.2)
6. ✅ Improve empty state (Fix 2.3)
7. ✅ Improve node positioning (Fix 2.5)

### Priority 3 (Medium - Nice to Have):
8. ✅ Add error boundary (Enhancement 3.1)
9. ✅ Add API validation (Enhancement 3.2)

---

## Files to Modify

### Backend (3 files):
1. `backend/app/services/operation_detector.py` - Enhance parsing + add fallback
2. `backend/app/services/judge.py` - Use fallback + add logging
3. `backend/app/services/executor.py` - (Optional) Ensure physical plan is extracted

### Frontend (4 files):
4. `frontend/src/components/QueryPlanViewer.jsx` - Better validation + debug
5. `frontend/src/components/DAGVisualization.jsx` - Better empty state + positioning
6. `frontend/src/components/DAGVisualization.css` - Fix height issues
7. `frontend/src/services/api.js` - (Optional) Validate response

---

## Estimated Time

- **Backend fixes**: 1-2 hours
- **Frontend fixes**: 1-2 hours
- **Testing**: 1 hour
- **Total**: 3-5 hours

---

## Rollout Plan

### Step 1: Backend Implementation
1. Implement Fix 1.1 (enhanced parsing)
2. Implement Fix 1.2 (fallback generation)
3. Update judge.py (Fix 1.3)
4. Test with Python to verify nodes/edges are generated

### Step 2: Frontend Implementation
1. Add defensive checks (Fix 2.1)
2. Fix CSS height (Fix 2.4)
3. Test in browser to verify rendering

### Step 3: Enhancements
1. Add debug logging (Fix 1.4, 2.2)
2. Improve empty states (Fix 2.3)
3. Better node positioning (Fix 2.5)

### Step 4: Testing & Validation
1. Test with 4 query types (see Testing Plan)
2. Verify all success criteria
3. Check console for errors
4. Verify visual appearance

---

## Debugging Checklist

If Visual DAG still doesn't work after fixes, check:

- [ ] Backend: `print(dag_structure)` shows nodes and edges
- [ ] Backend: Physical plan is not None or empty
- [ ] Backend: Nodes have all required fields (id, operation, depth, label)
- [ ] Frontend: Console shows dagStructure with nodes array
- [ ] Frontend: No console errors from ReactFlow
- [ ] Frontend: `.dag-visualization-container` has height > 0
- [ ] Frontend: `hasVisualData` is true
- [ ] Frontend: ReactFlow is imported correctly
- [ ] Browser: Hard refresh (Cmd+Shift+R) to clear cache
- [ ] Docker: Containers rebuilt with new code

---

**Status**: 📋 Plan Ready for Implementation
**Estimated Complexity**: Medium
**Risk Level**: Low (well-isolated changes)
**Expected Outcome**: Visual DAG displays correctly for all query types
