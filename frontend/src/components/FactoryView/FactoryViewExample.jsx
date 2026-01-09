import FactoryViewRedesigned from './FactoryViewRedesigned';

/**
 * Example usage of FactoryViewRedesigned with sample data
 * Use this for testing and demonstration purposes
 */

// Sample execution data - Simple job with shuffle
const sampleExecutionData = {
  total_duration: 6.5,

  stages: [
    {
      id: 0,
      name: "MapPartitionsRDD",
      operation_type: "map",
      parallelism: 4,
      tasks: [
        { id: "task-0-0", partition_id: 0, node_id: "executor-1", core_id: 0, start_time: 0.2, end_time: 1.8 },
        { id: "task-0-1", partition_id: 1, node_id: "executor-1", core_id: 1, start_time: 0.2, end_time: 1.7 },
        { id: "task-0-2", partition_id: 2, node_id: "executor-2", core_id: 0, start_time: 0.2, end_time: 1.9 },
        { id: "task-0-3", partition_id: 3, node_id: "executor-2", core_id: 1, start_time: 0.2, end_time: 1.8 }
      ]
    },
    {
      id: 1,
      name: "ShuffledRDD",
      operation_type: "groupByKey",
      parallelism: 4,
      tasks: [
        { id: "task-1-0", partition_id: 4, node_id: "executor-1", core_id: 0, start_time: 3.0, end_time: 5.2 },
        { id: "task-1-1", partition_id: 5, node_id: "executor-1", core_id: 1, start_time: 3.0, end_time: 5.0 },
        { id: "task-1-2", partition_id: 6, node_id: "executor-2", core_id: 0, start_time: 3.0, end_time: 5.3 },
        { id: "task-1-3", partition_id: 7, node_id: "executor-2", core_id: 1, start_time: 3.0, end_time: 5.1 }
      ]
    },
    {
      id: 2,
      name: "MapPartitionsRDD",
      operation_type: "reduce",
      parallelism: 2,
      tasks: [
        { id: "task-2-0", partition_id: 8, node_id: "executor-1", core_id: 0, start_time: 5.5, end_time: 6.2 },
        { id: "task-2-1", partition_id: 9, node_id: "executor-2", core_id: 0, start_time: 5.5, end_time: 6.3 }
      ]
    }
  ],

  nodes: [
    {
      id: "executor-1",
      name: "Executor-01",
      cores: 2,
      memory_gb: 8
    },
    {
      id: "executor-2",
      name: "Executor-02",
      cores: 2,
      memory_gb: 8
    }
  ],

  partitions: [
    // Stage 0 partitions
    { id: 0, stage_id: 0, size_mb: 85.3, records_count: 85300, parent_partitions: [], child_partitions: [4, 5] },
    { id: 1, stage_id: 0, size_mb: 92.1, records_count: 92100, parent_partitions: [], child_partitions: [4, 6] },
    { id: 2, stage_id: 0, size_mb: 78.5, records_count: 78500, parent_partitions: [], child_partitions: [5, 7] },
    { id: 3, stage_id: 0, size_mb: 88.7, records_count: 88700, parent_partitions: [], child_partitions: [6, 7] },

    // Stage 1 partitions (after shuffle)
    { id: 4, stage_id: 1, size_mb: 120.5, records_count: 120500, parent_partitions: [0, 1], child_partitions: [8] },
    { id: 5, stage_id: 1, size_mb: 115.2, records_count: 115200, parent_partitions: [0, 2], child_partitions: [8] },
    { id: 6, stage_id: 1, size_mb: 118.8, records_count: 118800, parent_partitions: [1, 3], child_partitions: [9] },
    { id: 7, stage_id: 1, size_mb: 122.3, records_count: 122300, parent_partitions: [2, 3], child_partitions: [9] },

    // Stage 2 partitions
    { id: 8, stage_id: 2, size_mb: 65.4, records_count: 65400, parent_partitions: [4, 5], child_partitions: [] },
    { id: 9, stage_id: 2, size_mb: 68.2, records_count: 68200, parent_partitions: [6, 7], child_partitions: [] }
  ],

  shuffles: [
    {
      id: "shuffle-0",
      from_stage_id: 0,
      to_stage_id: 1,
      data_volume_mb: 344.6
    }
  ],

  events: [
    // Stage 0 events
    { time: 0.0, event_type: "stage_start", stage_id: 0 },
    { time: 0.2, event_type: "task_start", stage_id: 0, task_id: "task-0-0" },
    { time: 0.2, event_type: "task_start", stage_id: 0, task_id: "task-0-1" },
    { time: 0.2, event_type: "task_start", stage_id: 0, task_id: "task-0-2" },
    { time: 0.2, event_type: "task_start", stage_id: 0, task_id: "task-0-3" },
    { time: 1.7, event_type: "task_end", stage_id: 0, task_id: "task-0-1" },
    { time: 1.8, event_type: "task_end", stage_id: 0, task_id: "task-0-0" },
    { time: 1.8, event_type: "task_end", stage_id: 0, task_id: "task-0-3" },
    { time: 1.9, event_type: "task_end", stage_id: 0, task_id: "task-0-2" },
    { time: 2.0, event_type: "stage_end", stage_id: 0 },

    // Shuffle events
    { time: 2.0, event_type: "shuffle_start", details: { from_stage: 0, to_stage: 1 } },
    { time: 2.8, event_type: "shuffle_end", details: { from_stage: 0, to_stage: 1 } },

    // Stage 1 events
    { time: 2.8, event_type: "stage_start", stage_id: 1 },
    { time: 3.0, event_type: "task_start", stage_id: 1, task_id: "task-1-0" },
    { time: 3.0, event_type: "task_start", stage_id: 1, task_id: "task-1-1" },
    { time: 3.0, event_type: "task_start", stage_id: 1, task_id: "task-1-2" },
    { time: 3.0, event_type: "task_start", stage_id: 1, task_id: "task-1-3" },
    { time: 5.0, event_type: "task_end", stage_id: 1, task_id: "task-1-1" },
    { time: 5.1, event_type: "task_end", stage_id: 1, task_id: "task-1-3" },
    { time: 5.2, event_type: "task_end", stage_id: 1, task_id: "task-1-0" },
    { time: 5.3, event_type: "task_end", stage_id: 1, task_id: "task-1-2" },
    { time: 5.4, event_type: "stage_end", stage_id: 1 },

    // Stage 2 events
    { time: 5.4, event_type: "stage_start", stage_id: 2 },
    { time: 5.5, event_type: "task_start", stage_id: 2, task_id: "task-2-0" },
    { time: 5.5, event_type: "task_start", stage_id: 2, task_id: "task-2-1" },
    { time: 6.2, event_type: "task_end", stage_id: 2, task_id: "task-2-0" },
    { time: 6.3, event_type: "task_end", stage_id: 2, task_id: "task-2-1" },
    { time: 6.4, event_type: "stage_end", stage_id: 2 }
  ],

  metrics: {
    total_shuffles: 1,
    total_data_processed_mb: 1488.8,
    skew_detected: false,
    cache_hits: 0,
    broadcast_used: false,
    cache_used: false
  }
};

// Sample with partition skew
const skewedExecutionData = {
  total_duration: 8.2,

  stages: [
    {
      id: 0,
      name: "GroupByKey",
      operation_type: "groupByKey",
      parallelism: 3,
      tasks: [
        { id: "task-0", partition_id: 0, node_id: "executor-1", core_id: 0, start_time: 0.1, end_time: 2.0 },
        { id: "task-1", partition_id: 1, node_id: "executor-2", core_id: 0, start_time: 0.1, end_time: 1.8 },
        { id: "task-2", partition_id: 2, node_id: "executor-3", core_id: 0, start_time: 0.1, end_time: 7.5 } // Straggler!
      ]
    }
  ],

  nodes: [
    { id: "executor-1", name: "Executor-01", cores: 1, memory_gb: 4 },
    { id: "executor-2", name: "Executor-02", cores: 1, memory_gb: 4 },
    { id: "executor-3", name: "Executor-03", cores: 1, memory_gb: 4 }
  ],

  partitions: [
    { id: 0, stage_id: 0, size_mb: 45.2, records_count: 45200, parent_partitions: [], child_partitions: [] },
    { id: 1, stage_id: 0, size_mb: 52.8, records_count: 52800, parent_partitions: [], child_partitions: [] },
    { id: 2, stage_id: 0, size_mb: 450.5, records_count: 450500, parent_partitions: [], child_partitions: [] } // Skewed!
  ],

  shuffles: [],

  events: [
    { time: 0.0, event_type: "stage_start", stage_id: 0 },
    { time: 0.1, event_type: "task_start", stage_id: 0, task_id: "task-0" },
    { time: 0.1, event_type: "task_start", stage_id: 0, task_id: "task-1" },
    { time: 0.1, event_type: "task_start", stage_id: 0, task_id: "task-2" },
    { time: 1.8, event_type: "task_end", stage_id: 0, task_id: "task-1" },
    { time: 2.0, event_type: "task_end", stage_id: 0, task_id: "task-0" },
    { time: 7.5, event_type: "task_end", stage_id: 0, task_id: "task-2" },
    { time: 7.6, event_type: "stage_end", stage_id: 0 }
  ],

  metrics: {
    total_shuffles: 0,
    skew_detected: true
  }
};

/**
 * Example Component
 */
function FactoryViewExample({ variant = "normal" }) {
  const data = variant === "skewed" ? skewedExecutionData : sampleExecutionData;

  return (
    <div style={{ width: '100%', minHeight: '100vh', padding: '20px' }}>
      <div style={{ marginBottom: '20px', padding: '20px', background: '#1a2234', borderRadius: '8px' }}>
        <h2 style={{ margin: '0 0 10px 0', color: '#06b6d4', fontFamily: 'Orbitron, monospace' }}>
          Factory View Example - {variant === "skewed" ? "Partition Skew" : "Normal Execution"}
        </h2>
        <p style={{ margin: 0, color: '#9ca3af', fontSize: '14px' }}>
          {variant === "skewed"
            ? "Watch one executor struggle with a massive partition while others sit idle!"
            : "Watch a typical Spark job with map, shuffle (groupByKey), and reduce stages."}
        </p>
      </div>

      <FactoryViewRedesigned simulationData={data} />

      <div style={{ marginTop: '20px', padding: '20px', background: '#1a2234', borderRadius: '8px' }}>
        <h3 style={{ margin: '0 0 10px 0', color: '#06b6d4', fontSize: '18px' }}>
          What to Watch For:
        </h3>
        <ul style={{ margin: 0, paddingLeft: '20px', color: '#9ca3af' }}>
          {variant === "skewed" ? (
            <>
              <li>Executor-03 has a partition 10x larger than the others</li>
              <li>Executors 1 & 2 finish quickly and go idle (gray)</li>
              <li>Executor-03's chip keeps pulsing cyan (still working)</li>
              <li>Red border appears on overloaded executor</li>
              <li>Cluster utilization drops to 33% while waiting</li>
            </>
          ) : (
            <>
              <li>Stage 0 (map): All partitions process in parallel - fast & efficient</li>
              <li>Orange SHUFFLE zone appears between Stage 0 and 1</li>
              <li>Particles flow slowly across the factory (expensive operation!)</li>
              <li>Stage 1 (groupByKey): Data redistributed to new partitions</li>
              <li>Stage 2 (reduce): Final aggregation with fewer partitions</li>
              <li>Green "Direct Flow" connectors for narrow transforms</li>
            </>
          )}
        </ul>
      </div>

      <div style={{ marginTop: '20px', padding: '20px', background: '#1a2234', borderRadius: '8px' }}>
        <h3 style={{ margin: '0 0 10px 0', color: '#06b6d4', fontSize: '18px' }}>
          Interactive Features:
        </h3>
        <ul style={{ margin: 0, paddingLeft: '20px', color: '#9ca3af' }}>
          <li>Click timeline to jump to any moment</li>
          <li>Hover partition chips to see details (size, records, lineage)</li>
          <li>Hover executors to highlight them in the sidebar</li>
          <li>Try different playback speeds (0.5x - 4x)</li>
          <li>Press spacebar to play/pause</li>
          <li>Watch the particle system during shuffles</li>
        </ul>
      </div>
    </div>
  );
}

export default FactoryViewExample;

// Export sample data for reuse
export { sampleExecutionData, skewedExecutionData };
