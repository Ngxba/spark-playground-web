# 📋 Backend Output Structure - Complete Guide

## Overview

The backend generates an `ExecutionSimulation` object that contains everything the frontend needs to visualize Spark execution. This document explains the complete structure with examples.

## 📁 Output Files Created

1. **`EXAMPLE_EXECUTION_OUTPUT.json`** - Complete example with 2 stages, 1 shuffle, full lineage
2. **`sample_execution_output.json`** - Simple single-stage example
3. **`multi_stage_execution_output.json`** - Multi-stage attempt

**👉 Open `EXAMPLE_EXECUTION_OUTPUT.json` for the best reference!**

---

## 🏗️ Data Structure

### Top-Level Object: ExecutionSimulation

```json
{
  "total_duration": 1.2,          // Total execution time in seconds
  "partition_count": 15,           // Total number of partitions across all stages
  "node_count": 4,                 // Number of worker nodes (executors)
  "cores_per_node": 4,            // CPU cores per executor
  "total_cores": 16,              // Total CPU cores available
  "stages": [...],                // Array of Stage objects
  "partitions": [...],            // Array of Partition objects WITH LINEAGE
  "shuffles": [...],              // Array of Shuffle objects WITH MAPPINGS
  "nodes": [...],                 // Array of Node (executor) objects
  "events": [...],                // Timeline events for animation
  "metrics": {...}                // Summary metrics
}
```

---

## 📦 Partition Object (KEY FEATURE: Lineage Tracking)

```json
{
  "id": 0,                        // Unique partition ID
  "size_mb": 2.5,                 // Partition size
  "records_count": 1000,          // Number of records
  "data_preview": null,           // Sample data (optional)

  // ⭐ NEW LINEAGE FIELDS ⭐
  "stage_id": 0,                  // Which stage this partition belongs to
  "parent_partitions": [],        // IDs of partitions this came from
  "child_partitions": [10, 11, 12, 13, 14]  // IDs of partitions this flows to
}
```

### Understanding Lineage

**Source Partitions (Stage 0):**
```json
{
  "id": 0,
  "stage_id": 0,
  "parent_partitions": [],              // Empty = source data (read from file)
  "child_partitions": [10, 11, 12, 13, 14]  // Flows to ALL Stage 1 partitions (shuffle)
}
```

**Destination Partitions (Stage 1, after shuffle):**
```json
{
  "id": 10,
  "stage_id": 1,
  "parent_partitions": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],  // Receives from ALL Stage 0 partitions
  "child_partitions": []                // Empty = final output
}
```

---

## 🔀 Shuffle Object (KEY FEATURE: Partition Mapping)

```json
{
  "from_stage_id": 0,             // Source stage
  "to_stage_id": 1,               // Destination stage
  "data_volume_mb": 25.0,         // Total data shuffled
  "from_partitions": 10,          // Source partition count
  "to_partitions": 5,             // Destination partition count
  "start_time": 0.5,              // When shuffle starts
  "end_time": 0.8,                // When shuffle ends

  // ⭐ NEW PARTITION MAPPING ⭐
  "partition_mapping": {
    "0": [10, 11, 12, 13, 14],    // Partition 0 sends to partitions 10-14
    "1": [10, 11, 12, 13, 14],    // Partition 1 sends to partitions 10-14
    "2": [10, 11, 12, 13, 14],    // etc... (all-to-all pattern)
    ...
  }
}
```

### Shuffle Patterns

**All-to-All (Hash Partitioning - groupBy, aggregate):**
```
Source:        Destination:
P0 ──┐
P1 ──┼──→ P10
P2 ──┤    P11
P3 ──┤    P12
P4 ──┘    P13
          P14
Each source sends to ALL destinations
```

**One-to-One (Narrow Dependency - map, filter):**
```
NO SHUFFLE - direct mapping
P0 → P5
P1 → P6
P2 → P7
```

---

## ⚙️ Task Object (Executor Assignment)

```json
{
  "id": 0,                        // Task ID
  "partition_id": 0,              // Which partition this task processes
  "node_id": 0,                   // Which executor (Worker 1, Worker 2, etc.)
  "core_id": 0,                   // Which core on the executor
  "start_time": 0.0,              // When task starts
  "end_time": 0.5,                // When task completes
  "duration": 0.5,                // Task duration
  "status": "completed"           // pending, running, completed, failed
}
```

### How Frontend Uses Task Info

```javascript
// Frontend looks up which executor is processing partition 0:
const task = stage.tasks.find(t => t.partition_id === 0);
const executor = nodes.find(n => n.id === task.node_id);
// Result: Worker 1, Core 0
```

---

## 💻 Node Object (Executor Info)

```json
{
  "id": 0,                        // Node ID
  "name": "Worker 1",             // Display name
  "cores": 4,                     // Number of CPU cores
  "memory_gb": 4.0,              // Available memory
  "assigned_tasks": [0, 1, 10, 11]  // Task IDs assigned to this executor
}
```

---

## 🏭 Stage Object

```json
{
  "id": 0,                        // Stage ID
  "name": "Scan + Filter",        // Stage description
  "operation_type": "scan",       // scan, filter, join, aggregate, shuffle
  "start_time": 0.0,              // Stage start time
  "end_time": 0.5,                // Stage end time
  "tasks": [...],                 // Array of Task objects
  "dependencies": [],             // IDs of parent stages
  "parallelism": 10,              // Degree of parallelism
  "status": "completed"           // pending, running, completed
}
```

---

## 🎬 SimulationEvent Object (Timeline Animation)

```json
{
  "time": 0.0,                    // Event timestamp
  "event_type": "task_start",     // Event type
  "stage_id": 0,                  // Related stage
  "task_id": 0,                   // Related task
  "details": {                    // Additional context
    "partition": 0,
    "node": 0
  }
}
```

### Event Types

- `stage_start` - Stage begins
- `stage_end` - Stage completes
- `task_start` - Task begins processing
- `task_end` - Task completes
- `shuffle_start` - Shuffle operation starts
- `shuffle_end` - Shuffle operation completes

---

## 📊 How Frontend Uses This Data

### 1. ExecutionDiagram Component

**Shows partitions with executor assignments:**

```javascript
// For each partition, find which executor processes it
const task = getTaskForPartition(partition.id);
const executor = getExecutorForTask(task);

// Display:
// Partition 0
// 📍 Executor: Worker 1
// Core 0
```

**Shows partition lineage on hover:**

```javascript
// When hovering partition 10:
// Parents: P0, P1, P2, P3, P4, P5, P6, P7, P8, P9
// Children: (none - final output)
```

### 2. Shuffle Visualization

```javascript
// Display shuffle boundary:
const shuffle = getShuffleBetween(stage0.id, stage1.id);

// Shows:
// 🔀 SHUFFLE BOUNDARY
// Data Volume: 25.0 MB
// Redistribution: 10 → 5 partitions
// All-to-All Pattern
```

### 3. Particle Animation

```javascript
// For each partition:
partition.child_partitions.forEach(childId => {
  const isShuffle = childPartition.stage_id !== partition.stage_id;

  // Spawn particles:
  // - Blue particles for narrow dependencies
  // - Orange particles for shuffles
});
```

### 4. Executor Summary

```javascript
// For each executor:
nodes.forEach(node => {
  const activeTasks = currentState.tasksByNode[node.id].active;

  // Display:
  // Worker 1 (4 cores, 4.0GB)
  // Processing: P0, P4, P8, P10
});
```

---

## 🎯 Example Query Walkthrough

### Query: `df.groupBy("category").count()`

**What Backend Generates:**

```
Stage 0: Scan + Filter (10 partitions)
├─ Partitions: P0-P9
├─ Each partition has child_partitions: [10, 11, 12, 13, 14]
└─ Tasks assigned to Workers 1-4

Shuffle: Stage 0 → Stage 1
├─ Data Volume: 25.0 MB
├─ Partition Mapping: All-to-All
│  P0 → [10, 11, 12, 13, 14]
│  P1 → [10, 11, 12, 13, 14]
│  ... (each source goes to all destinations)
└─ Duration: 0.5s → 0.8s

Stage 1: HashAggregate (5 partitions)
├─ Partitions: P10-P14
├─ Each partition has parent_partitions: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
└─ Tasks assigned to Workers 1-4
```

**What Frontend Shows:**

1. ✅ 10 partitions in Stage 0, each showing which executor processes it
2. ✅ Shuffle boundary with "All-to-All" pattern visualization
3. ✅ 5 partitions in Stage 1, each receiving from all Stage 0 partitions
4. ✅ Orange particles flowing from all Stage 0 → all Stage 1 partitions
5. ✅ Executor summary showing which partitions each worker processes

---

## 🔍 Discussion Points

### 1. Cache Information

**Current State:**
- Cache detection exists in `operation_detector.py`
- Looks for `InMemoryRelation` in physical plan
- Sets `cache_used: bool` in metrics

**What's Missing:**
- Which specific DataFrames are cached
- Which stages read from cache vs disk
- Cache memory usage

**Potential Enhancement:**
```json
{
  "cached_dataframes": [
    {
      "name": "df_filtered",
      "size_mb": 50.0,
      "partitions": [0, 1, 2, 3, 4],
      "storage_level": "MEMORY_AND_DISK"
    }
  ]
}
```

### 2. Partition Skew

**Not currently tracked:**
- Actual partition sizes can vary widely
- Some partitions might be 10MB, others 0.1MB
- This causes slow tasks (stragglers)

**Potential Enhancement:**
```json
{
  "partition_skew": {
    "min_size_mb": 0.5,
    "max_size_mb": 15.0,
    "median_size_mb": 2.5,
    "skewed_partitions": [4, 7]  // IDs of unusually large partitions
  }
}
```

### 3. Network Transfer Details

**Current:** Only total shuffle volume
**Could Add:**
```json
{
  "network_transfer": {
    "total_bytes": 26214400,
    "per_partition": {
      "0": {"bytes_sent": 2621440, "destinations": [10, 11, 12, 13, 14]},
      "1": {"bytes_sent": 2621440, "destinations": [10, 11, 12, 13, 14]}
    }
  }
}
```

---

## ✅ Summary

The backend now provides:

1. ✅ **Complete partition lineage** (parent/child relationships)
2. ✅ **Shuffle mappings** (which partitions go where)
3. ✅ **Executor assignments** (which worker/core processes each partition)
4. ✅ **Timeline events** (for animation)
5. ✅ **Cache detection** (basic - can be enhanced)

**📄 Files to examine:**
- `EXAMPLE_EXECUTION_OUTPUT.json` - Complete 2-stage example
- `backend/app/models/execution.py` - Model definitions
- `backend/app/services/execution_simulator.py` - Generation logic
- `frontend/src/components/FactoryView/ExecutionDiagram.jsx` - How frontend uses the data

**🎯 Next steps for discussion:**
- Cache information enhancement
- Partition skew tracking
- Network transfer details
- Performance metrics per partition
