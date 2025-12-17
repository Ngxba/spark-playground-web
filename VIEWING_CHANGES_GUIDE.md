# How to View the Frontend Enhancements

## Current Status
- ✅ Frontend running on: **http://localhost:5174/**
- ✅ Backend running on: **http://localhost:8000/**
- ✅ All components built and ready

## Where to See the Changes

### 1. ReferencePanel (Visible Immediately)
**Location:** Any puzzle workspace page

**Steps to see it:**
1. Open http://localhost:5174/
2. Click on any puzzle (e.g., "Fast Join")
3. Look at the **left panel below the factory visualization**
4. You should see a purple button that says "**▶ Spark Reference**"
5. Click it to expand the collapsible reference panel

**What you'll see:**
- Tabbed interface with: Transformations, Actions, Optimizations, Best Practices
- Code examples for each function
- Tips and descriptions

---

### 2. Enhanced RunReport Modal (Visible After Running Code)
**Location:** Appears after clicking "Run Factory"

**Steps to see it:**
1. Navigate to a puzzle (http://localhost:5174/puzzle/fast_join)
2. Write or use the starter code
3. Click "**▶ Run Factory**" button
4. Wait for execution to complete
5. The **enhanced modal** will appear with 5 tabs

**What you'll see:**

#### Tab 1: Overview
- Performance metrics with **hover tooltips** (hover over metrics to see educational info)
- Star rating in header
- Execution log

#### Tab 2: Results
- **Interactive sortable table**
- Search bar to filter results
- Click column headers to sort
- Side-by-side comparison if output is incorrect

#### Tab 3: Insights
- **Execution Summary** with visual cards
- **Optimizations Applied** (green cards showing broadcast/cache usage)
- **Optimization Opportunities** (yellow cards with suggestions)

#### Tab 4: Query Plan
- Three views:
  - **Visual DAG**: Interactive node graph (zoom, pan, click)
  - **Physical Plan**: Syntax-highlighted with color coding
  - **Logical Plan**: Formatted plan text

#### Tab 5: Hints
- **Progressive hint system** with 4 levels
- Click dots or "Show More" to reveal hints gradually
- Level 4 shows before/after code examples

---

## Quick Test

### Test the ReferencePanel:
```
1. Go to: http://localhost:5174/puzzle/fast_join
2. Look for purple button: "▶ Spark Reference"
3. Click to expand
4. Click through the tabs
```

### Test the Enhanced RunReport:
```
1. On the puzzle page, click "▶ Run Factory"
2. Wait for modal to appear
3. Click through all 5 tabs:
   - Overview → Results → Insights → Query Plan → Hints
4. Try:
   - Hovering over metrics in Overview
   - Sorting columns in Results tab
   - Clicking nodes in Query Plan's Visual DAG
   - Progressing through hint levels in Hints tab
```

---

## Troubleshooting

### If you don't see the ReferencePanel:
1. Hard refresh: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)
2. Clear browser cache
3. Check browser console for errors (F12)

### If the RunReport doesn't show new tabs:
1. Make sure you clicked "Run Factory" and execution completed
2. Check if modal appears at all
3. Look for any console errors

### If backend isn't responding:
```bash
# Check backend status
docker-compose ps

# View backend logs
docker-compose logs backend --tail=50

# Restart backend if needed
docker-compose restart backend
```

### If frontend has errors:
```bash
# Check dev server output
# Look for any red error messages

# Try rebuilding
npm run build

# Restart dev server
# Kill the process and run: npm run dev
```

---

## Visual Checklist

### What's Different:

#### Before:
- ❌ Single-view run report
- ❌ Raw metrics without explanations
- ❌ No query plan visualization
- ❌ Single-level hints
- ❌ No reference documentation

#### After:
- ✅ 5-tab run report with rich information
- ✅ Interactive tooltips on all metrics
- ✅ Visual DAG + syntax-highlighted plans
- ✅ Progressive 4-level hints
- ✅ Collapsible Spark reference panel
- ✅ Interactive sortable results table
- ✅ Detailed execution insights
- ✅ Before/after code examples

---

## Screenshots Locations to Check

### Location 1: Main Workspace
- **URL:** http://localhost:5174/puzzle/fast_join
- **Look for:** Purple "Spark Reference" button below factory visualization
- **Action:** Click to expand

### Location 2: Run Report - Overview Tab
- **When:** After clicking "Run Factory"
- **Look for:** Tabs at top: Overview | Results | Insights | Query Plan | Hints
- **Action:** Hover over "Shuffles" or "Stages" metrics to see tooltips

### Location 3: Run Report - Results Tab
- **When:** Click "Results" tab in modal
- **Look for:** Sortable table with search bar
- **Action:** Click column headers, try searching

### Location 4: Run Report - Insights Tab
- **When:** Click "Insights" tab
- **Look for:** Colored cards showing optimizations and suggestions
- **Visual:** Green cards = good, Yellow cards = opportunities

### Location 5: Run Report - Query Plan Tab
- **When:** Click "Query Plan" tab
- **Look for:** Three sub-tabs and interactive graph
- **Action:** Drag, zoom, pan the DAG graph

### Location 6: Run Report - Hints Tab
- **When:** Click "Hints" tab
- **Look for:** Numbered dots at top (1, 2, 3, 4)
- **Action:** Click dots or "Show More" button

---

## Expected Behavior

### Interactive Elements:
1. **Metric Tooltips**: Hover shows explanation + examples
2. **Results Table**: Click headers to sort, type to search
3. **DAG Graph**: Drag to pan, scroll to zoom, click nodes
4. **Hint Levels**: Click dots to jump between levels
5. **Reference Panel**: Click tabs to switch sections

### Visual Feedback:
- Hover effects on all interactive elements
- Smooth tab transitions
- Color-coded operations (green/yellow/blue)
- Animated hint transitions

---

## If You Still Don't See Changes

1. **Verify the files exist:**
   ```bash
   ls -la frontend/src/components/ | grep -E "Query|DAG|Execution|Results|Metric|Progressive|Reference"
   ```

2. **Check if components are imported:**
   ```bash
   grep -r "import.*QueryPlanViewer" frontend/src/
   grep -r "import.*ReferencePanel" frontend/src/
   ```

3. **Verify build includes new files:**
   ```bash
   npm run build
   # Should show no errors and include new components
   ```

4. **Check browser console** (F12 > Console tab):
   - Look for any red errors
   - Check Network tab for failed requests

5. **Try incognito/private mode:**
   - Eliminates cache issues
   - Fresh load of all components

---

## Contact Points

If changes still aren't visible:
1. Share screenshot of the puzzle workspace page
2. Share screenshot of the modal after running code
3. Share browser console errors (F12 > Console)
4. Confirm URLs you're visiting

---

**Last Updated:** 2025-12-08
**Frontend Status:** ✅ Running on localhost:5174
**Backend Status:** ✅ Running on localhost:8000 (docker)
