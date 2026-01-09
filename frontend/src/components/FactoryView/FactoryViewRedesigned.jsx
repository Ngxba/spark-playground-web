import { useState, useEffect, useRef, useMemo } from 'react';
import './FactoryViewRedesigned.css';

/**
 * FactoryView - COMPLETE REDESIGN
 * Mission Control Blueprint Aesthetic
 * Real-time Spark execution visualizer with factory floor metaphor
 */
function FactoryViewRedesigned({ simulationData }) {
  const [currentTime, setCurrentTime] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [currentState, setCurrentState] = useState(null);
  const [hoveredPartition, setHoveredPartition] = useState(null);
  const [hoveredExecutor, setHoveredExecutor] = useState(null);
  const canvasRef = useRef(null);
  const animationFrameRef = useRef(null);
  const particlesRef = useRef([]);

  // Empty state
  if (!simulationData) {
    return (
      <div className="fv-container fv-empty">
        <div className="fv-empty-content">
          <div className="fv-empty-icon">⚡</div>
          <h3 className="fv-empty-title">EXECUTION FACTORY OFFLINE</h3>
          <p className="fv-empty-desc">
            Run a Spark query to activate the factory floor visualization.
            Watch your data flow through the cluster in real-time.
          </p>
          <div className="fv-empty-features">
            <div className="fv-empty-feature">
              <div className="fv-empty-feature-icon">◯</div>
              <div className="fv-empty-feature-label">Stage Execution</div>
            </div>
            <div className="fv-empty-feature">
              <div className="fv-empty-feature-icon">◬</div>
              <div className="fv-empty-feature-label">Partition Tracking</div>
            </div>
            <div className="fv-empty-feature">
              <div className="fv-empty-feature-icon">▦</div>
              <div className="fv-empty-feature-label">Executor Monitoring</div>
            </div>
          </div>
        </div>
        <div className="fv-scanline"></div>
      </div>
    );
  }

  const { total_duration, stages, nodes, events, partitions = [], shuffles = [], metrics = {} } = simulationData;

  // Auto-play on mount
  useEffect(() => {
    if (simulationData && !isPlaying && currentTime === 0) {
      setIsPlaying(true);
    }
  }, [simulationData]);

  // Calculate execution state
  useEffect(() => {
    if (!simulationData) return;
    const state = calculateExecutionState(currentTime, simulationData);
    setCurrentState(state);
  }, [currentTime, simulationData]);

  // Animation loop
  useEffect(() => {
    if (!isPlaying) return;

    const interval = setInterval(() => {
      setCurrentTime((prevTime) => {
        const nextTime = prevTime + (0.016 * playbackSpeed);
        if (nextTime >= total_duration) {
          setIsPlaying(false);
          return total_duration;
        }
        return nextTime;
      });
    }, 16);

    return () => clearInterval(interval);
  }, [isPlaying, playbackSpeed, total_duration]);

  // Canvas particle system for shuffles
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !currentState) return;

    const ctx = canvas.getContext('2d');
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * window.devicePixelRatio;
    canvas.height = rect.height * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);

    const animate = () => {
      ctx.clearRect(0, 0, rect.width, rect.height);

      // Draw particles for active shuffles
      if (currentState.activeShuffles && currentState.activeShuffles.length > 0) {
        currentState.activeShuffles.forEach((shuffle, idx) => {
          drawShuffleParticles(ctx, rect, shuffle, idx);
        });
      }

      animationFrameRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [currentState]);

  const drawShuffleParticles = (ctx, rect, shuffle, shuffleIndex) => {
    const particleCount = 20;
    const baseY = shuffleIndex * 400 + 300; // Position based on shuffle index

    for (let i = 0; i < particleCount; i++) {
      const progress = ((currentTime * 1000 + i * 100) % 1500) / 1500;
      const x = progress * rect.width;
      const y = baseY + Math.sin(progress * Math.PI * 2) * 20;

      const alpha = Math.sin(progress * Math.PI);

      ctx.beginPath();
      ctx.arc(x, y, 3, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(251, 146, 60, ${alpha * 0.8})`;
      ctx.fill();

      ctx.beginPath();
      ctx.arc(x, y, 6, 0, Math.PI * 2);
      ctx.strokeStyle = `rgba(251, 146, 60, ${alpha * 0.3})`;
      ctx.lineWidth = 1;
      ctx.stroke();
    }
  };

  const handlePlayPause = () => setIsPlaying(!isPlaying);
  const handleReset = () => {
    setCurrentTime(0);
    setIsPlaying(false);
  };
  const handleSpeedChange = (speed) => setPlaybackSpeed(speed);
  const handleSeek = (time) => setCurrentTime(time);

  const progress = total_duration > 0 ? (currentTime / total_duration) * 100 : 0;
  const jobStatus = currentTime >= total_duration ? 'completed' : isPlaying ? 'running' : 'paused';

  // Calculate stage segments for timeline
  const stageSegments = useMemo(() => {
    if (!stages || !events || stages.length === 0) return [];

    const segments = [];
    for (let i = 0; i < stages.length; i++) {
      const stage = stages[i];
      const stageStartEvent = events.find(
        e => e.event_type === 'stage_start' && e.stage_id === stage.id
      );

      let stageEnd = total_duration;
      if (i < stages.length - 1) {
        const nextStage = stages[i + 1];
        const nextStageStart = events.find(
          e => e.event_type === 'stage_start' && e.stage_id === nextStage.id
        );
        if (nextStageStart) {
          stageEnd = nextStageStart.time;
        }
      }

      if (stageStartEvent) {
        const startPercent = (stageStartEvent.time / total_duration) * 100;
        const endPercent = (stageEnd / total_duration) * 100;
        const widthPercent = endPercent - startPercent;

        segments.push({
          stage,
          index: i,
          startTime: stageStartEvent.time,
          endTime: stageEnd,
          startPercent,
          endPercent,
          widthPercent,
          duration: stageEnd - stageStartEvent.time
        });
      }
    }
    return segments;
  }, [stages, events, total_duration]);

  // Find shuffle events
  const shuffleMarkers = useMemo(() => {
    if (!events) return [];
    return events
      .filter(e => e.event_type === 'shuffle_start')
      .map(e => ({
        time: e.time,
        position: (e.time / total_duration) * 100,
        details: e.details
      }));
  }, [events, total_duration]);

  return (
    <div className="fv-container">
      {/* Background effects */}
      <div className="fv-grid-bg"></div>
      <canvas ref={canvasRef} className="fv-particle-canvas"></canvas>
      <div className="fv-scanline"></div>

      {/* Control Tower Header */}
      <header className="fv-header">
        <div className="fv-header-left">
          <div className="fv-title-group">
            <div className="fv-title-icon">⚡</div>
            <div className="fv-title-text">EXECUTION FACTORY</div>
          </div>
          <div className="fv-subtitle">Real-time distributed execution monitor</div>
        </div>

        <div className="fv-header-center">
          <div className={`fv-status fv-status-${jobStatus}`}>
            <div className="fv-status-indicator"></div>
            <span className="fv-status-text">{jobStatus.toUpperCase()}</span>
          </div>
        </div>

        <div className="fv-header-right">
          <button
            className="fv-btn fv-btn-reset"
            onClick={handleReset}
            aria-label="Reset to start"
          >
            ↺ RESET
          </button>
          <button
            className={`fv-btn fv-btn-play ${isPlaying ? 'fv-btn-active' : ''}`}
            onClick={handlePlayPause}
            aria-label={isPlaying ? 'Pause' : 'Play'}
          >
            {isPlaying ? '⏸ PAUSE' : '▶ PLAY'}
          </button>
          <div className="fv-speed-group">
            <span className="fv-speed-label">SPEED</span>
            {[0.5, 1, 2, 4].map(speed => (
              <button
                key={speed}
                className={`fv-speed-btn ${playbackSpeed === speed ? 'fv-speed-active' : ''}`}
                onClick={() => handleSpeedChange(speed)}
                aria-label={`${speed}x speed`}
              >
                {speed}x
              </button>
            ))}
          </div>
        </div>
      </header>

      {/* Timeline Ruler */}
      <div className="fv-timeline">
        {/* Stage Markers Row (Above Timeline) */}
        <div className="fv-timeline-stage-markers">
          {stageSegments.map((segment) => (
            <div
              key={segment.stage.id}
              className="fv-stage-marker"
              style={{ left: `${segment.startPercent}%` }}
              onClick={() => handleSeek(segment.startTime)}
              title={`Stage ${segment.stage.id}: ${segment.stage.operation_type || segment.stage.name}`}
            >
              <div className="fv-stage-marker-label">S{segment.stage.id}</div>
              <div className="fv-stage-marker-line"></div>
            </div>
          ))}
        </div>

        {/* Timeline Track */}
        <div className="fv-timeline-track" onClick={(e) => {
          const rect = e.currentTarget.getBoundingClientRect();
          const clickX = e.clientX - rect.left;
          const newTime = (clickX / rect.width) * total_duration;
          handleSeek(newTime);
        }}>
          {/* Stage Segments Background */}
          {stageSegments.map((segment, idx) => (
            <div
              key={segment.stage.id}
              className={`fv-timeline-segment fv-timeline-segment-${segment.stage.operation_type?.toLowerCase().includes('group') || segment.stage.operation_type?.toLowerCase().includes('join') ? 'wide' : 'narrow'}`}
              style={{
                left: `${segment.startPercent}%`,
                width: `${segment.widthPercent}%`
              }}
              title={`Stage ${segment.stage.id}: ${segment.stage.operation_type || segment.stage.name} (${segment.duration.toFixed(2)}s)`}
            ></div>
          ))}

          {/* Progress Overlay */}
          <div className="fv-timeline-progress" style={{ width: `${progress}%` }}></div>

          {/* Scrubber Handle */}
          <div className="fv-timeline-scrubber" style={{ left: `${progress}%` }}>
            <div className="fv-timeline-handle"></div>
          </div>

          {/* Shuffle Markers */}
          {shuffleMarkers.map((shuffle, idx) => (
            <div
              key={idx}
              className="fv-timeline-shuffle-marker"
              style={{ left: `${shuffle.position}%` }}
              title={`Shuffle at ${shuffle.time.toFixed(2)}s`}
              onClick={(e) => {
                e.stopPropagation();
                handleSeek(shuffle.time);
              }}
            >
              <div className="fv-shuffle-marker-icon">⚡</div>
            </div>
          ))}

          {/* Time markers */}
          <div className="fv-timeline-markers">
            {Array.from({ length: Math.ceil(total_duration) + 1 }).map((_, i) => (
              <div
                key={i}
                className="fv-timeline-marker"
                style={{ left: `${(i / total_duration) * 100}%` }}
              >
                <div className="fv-timeline-tick"></div>
                <div className="fv-timeline-label">{i}s</div>
              </div>
            ))}
          </div>
        </div>

        <div className="fv-timeline-time">
          <span className="fv-timeline-current">{currentTime.toFixed(2)}s</span>
          <span className="fv-timeline-divider">/</span>
          <span className="fv-timeline-total">{total_duration.toFixed(2)}s</span>
        </div>
      </div>

      {/* Main Content */}
      <div className="fv-content">
        {/* Factory Floor */}
        <div className="fv-factory-floor">
          <div className="fv-floor-header">
            <span className="fv-floor-title">◬ FACTORY FLOOR</span>
            <span className="fv-floor-info">{stages?.length || 0} Production Stages</span>
          </div>

          <div className="fv-stages-container">
            {stages && stages.map((stage, stageIdx) => (
              <StageZone
                key={stage.id}
                stage={stage}
                stageIndex={stageIdx}
                nodes={nodes}
                partitions={partitions.filter(p => p.stage_id === stage.id)}
                currentState={currentState}
                nextStage={stages[stageIdx + 1]}
                shuffle={shuffles?.find(s => s.from_stage_id === stage.id)}
                hoveredPartition={hoveredPartition}
                setHoveredPartition={setHoveredPartition}
                hoveredExecutor={hoveredExecutor}
                setHoveredExecutor={setHoveredExecutor}
              />
            ))}
          </div>
        </div>

        {/* Monitoring Sidebar */}
        <aside className="fv-sidebar">
          <LiveMetricsPanel
            currentState={currentState}
            metrics={metrics}
            currentTime={currentTime}
            playbackSpeed={playbackSpeed}
          />

          <ClusterHealthPanel
            nodes={nodes}
            currentState={currentState}
            hoveredExecutor={hoveredExecutor}
            setHoveredExecutor={setHoveredExecutor}
          />

          <StageOverviewPanel
            stages={stages}
            currentState={currentState}
            currentTime={currentTime}
          />
        </aside>
      </div>
    </div>
  );
}

/**
 * Stage Zone - Individual production phase
 */
function StageZone({
  stage,
  stageIndex,
  nodes,
  partitions,
  currentState,
  nextStage,
  shuffle,
  hoveredPartition,
  setHoveredPartition,
  hoveredExecutor,
  setHoveredExecutor
}) {
  const isActive = currentState?.activeStages?.includes(stage.id);
  const tasks = stage.tasks || [];

  const completedTasks = tasks.filter(t =>
    currentState?.completedTasks?.some(ct => ct.id === t.id)
  ).length;
  const completionPercent = tasks.length > 0 ? (completedTasks / tasks.length) * 100 : 0;

  const stageTypeClass = stage.operation_type?.toLowerCase().includes('group') ||
                         stage.operation_type?.toLowerCase().includes('join') ? 'fv-stage-wide' : 'fv-stage-narrow';

  return (
    <>
      <div className={`fv-stage ${stageTypeClass} ${isActive ? 'fv-stage-active' : ''}`}>
        {/* Stage Header */}
        <div className="fv-stage-header">
          <div className="fv-stage-id">
            <span className="fv-stage-id-label">STAGE</span>
            <span className="fv-stage-id-number">{stage.id}</span>
          </div>

          <div className="fv-stage-info">
            <div className="fv-stage-name">{stage.name}</div>
            <div className="fv-stage-operation">{stage.operation_type}</div>
          </div>

          <div className="fv-stage-progress-wrapper">
            <div className="fv-stage-progress-bar">
              <div
                className="fv-stage-progress-fill"
                style={{ width: `${completionPercent}%` }}
              ></div>
            </div>
            <div className="fv-stage-progress-text">
              {completedTasks}/{tasks.length}
            </div>
          </div>
        </div>

        {/* Partition Queue Overview */}
        <PartitionQueue
          stage={stage}
          partitions={partitions}
          currentState={currentState}
          hoveredPartition={hoveredPartition}
          setHoveredPartition={setHoveredPartition}
        />

        {/* Executor Grid */}
        <div className="fv-executor-grid">
          {nodes && nodes.map(node => (
            <ExecutorMachine
              key={node.id}
              node={node}
              stage={stage}
              partitions={partitions}
              currentState={currentState}
              hoveredPartition={hoveredPartition}
              setHoveredPartition={setHoveredPartition}
              hoveredExecutor={hoveredExecutor}
              setHoveredExecutor={setHoveredExecutor}
            />
          ))}
        </div>
      </div>

      {/* Shuffle Connector */}
      {shuffle && nextStage && (
        <div className="fv-shuffle-zone">
          <div className="fv-shuffle-warning">
            <div className="fv-shuffle-icon">⚡</div>
            <div className="fv-shuffle-label">SHUFFLE OPERATION</div>
          </div>
          <div className="fv-shuffle-stats">
            <div className="fv-shuffle-stat">
              <span className="fv-shuffle-value">{shuffle.data_volume_mb?.toFixed(1) || 0}</span>
              <span className="fv-shuffle-unit">MB</span>
            </div>
            <div className="fv-shuffle-arrow">→</div>
            <div className="fv-shuffle-stat">
              <span className="fv-shuffle-value">{partitions.length}</span>
              <span className="fv-shuffle-unit">to</span>
              <span className="fv-shuffle-value">{nodes?.length || 0}</span>
            </div>
          </div>
          <div className="fv-shuffle-flow-line"></div>
        </div>
      )}

      {/* Narrow Connector */}
      {!shuffle && nextStage && (
        <div className="fv-narrow-connector">
          <div className="fv-narrow-line"></div>
          <div className="fv-narrow-label">Direct Flow</div>
        </div>
      )}
    </>
  );
}

/**
 * Partition Queue - Shows all partitions for the stage with their states
 */
function PartitionQueue({ stage, partitions, currentState, hoveredPartition, setHoveredPartition }) {
  const tasks = stage.tasks || [];

  // Get all partitions for this stage
  const stagePartitions = partitions.filter(p => p.stage_id === stage.id);

  // Categorize tasks by state
  const runningTasks = tasks.filter(t => currentState?.activeTasks?.some(at => at.id === t.id));
  const completedTasks = tasks.filter(t => currentState?.completedTasks?.some(ct => ct.id === t.id));
  const pendingTasks = tasks.filter(t =>
    !currentState?.activeTasks?.some(at => at.id === t.id) &&
    !currentState?.completedTasks?.some(ct => ct.id === t.id)
  );

  // Helper to get partition state
  const getPartitionState = (partition) => {
    const task = tasks.find(t => t.partition_id === partition.id);
    if (!task) return 'pending';

    if (currentState?.activeTasks?.some(at => at.id === task.id)) return 'running';
    if (currentState?.completedTasks?.some(ct => ct.id === task.id)) return 'completed';
    return 'pending';
  };

  return (
    <div className="fv-partition-queue">
      <div className="fv-partition-queue-header">
        <span className="fv-partition-queue-title">PARTITION PIPELINE</span>
        <div className="fv-partition-queue-stats">
          <span className="fv-queue-stat fv-queue-stat-running">
            <span className="fv-queue-stat-icon">▶</span>
            {runningTasks.length} Running
          </span>
          <span className="fv-queue-stat fv-queue-stat-pending">
            <span className="fv-queue-stat-icon">◷</span>
            {pendingTasks.length} Queued
          </span>
          <span className="fv-queue-stat fv-queue-stat-completed">
            <span className="fv-queue-stat-icon">✓</span>
            {completedTasks.length} Done
          </span>
        </div>
      </div>

      <div className="fv-partition-queue-items">
        {stagePartitions.map(partition => {
          const state = getPartitionState(partition);
          const isHovered = hoveredPartition === partition.id;

          return (
            <div
              key={partition.id}
              className={`fv-queue-partition fv-queue-partition-${state} ${isHovered ? 'fv-queue-partition-hovered' : ''}`}
              onMouseEnter={() => setHoveredPartition(partition.id)}
              onMouseLeave={() => setHoveredPartition(null)}
              title={`Partition ${partition.id} - ${state.toUpperCase()}`}
            >
              <div className="fv-queue-partition-id">P{partition.id}</div>
              {state === 'running' && <div className="fv-queue-partition-pulse"></div>}
              {state === 'completed' && <div className="fv-queue-partition-check">✓</div>}
            </div>
          );
        })}
      </div>
    </div>
  );
}

/**
 * Executor Machine - Processing workstation
 */
function ExecutorMachine({
  node,
  stage,
  partitions,
  currentState,
  hoveredPartition,
  setHoveredPartition,
  hoveredExecutor,
  setHoveredExecutor
}) {
  const stageTasks = stage.tasks?.filter(t => t.node_id === node.id) || [];
  const activeTasks = stageTasks.filter(t =>
    currentState?.activeTasks?.some(at => at.id === t.id)
  );
  const completedTasks = stageTasks.filter(t =>
    currentState?.completedTasks?.some(ct => ct.id === t.id)
  );

  const isHovered = hoveredExecutor === node.id;
  const utilization = stageTasks.length > 0 ? (activeTasks.length / node.cores) * 100 : 0;
  const isOverloaded = utilization > 90;

  return (
    <div
      className={`fv-executor ${isHovered ? 'fv-executor-hovered' : ''} ${isOverloaded ? 'fv-executor-overload' : ''}`}
      onMouseEnter={() => setHoveredExecutor(node.id)}
      onMouseLeave={() => setHoveredExecutor(null)}
    >
      <div className="fv-executor-header">
        <span className="fv-executor-name">{node.name}</span>
        <span className="fv-executor-cores">{node.cores} CORES</span>
      </div>

      <div className="fv-cores-grid">
        {Array.from({ length: node.cores }).map((_, coreIdx) => {
          // Find task assigned to this core
          const coreTask = stageTasks.find(t => t.core_id === coreIdx);

          // Find partition for this task
          let partition = null;
          if (coreTask && coreTask.partition_id !== undefined) {
            partition = partitions.find(p => p.id === coreTask.partition_id);
          }

          // Check task state
          const isActive = coreTask && currentState?.activeTasks?.some(t => t.id === coreTask.id);
          const isCompleted = coreTask && currentState?.completedTasks?.some(t => t.id === coreTask.id);

          // Debug: Log when partition should exist but doesn't
          if (coreTask && coreTask.partition_id !== undefined && !partition) {
            console.warn(`Missing partition ${coreTask.partition_id} for task ${coreTask.id} on stage ${stage.id}, node ${node.id}, core ${coreIdx}`);
            console.log('Available partitions:', partitions.map(p => p.id));
          }

          return (
            <div key={coreIdx} className={`fv-core ${isActive ? 'fv-core-active' : isCompleted ? 'fv-core-complete' : ''}`}>
              {partition && (
                <PartitionChip
                  partition={partition}
                  isActive={isActive}
                  isCompleted={isCompleted}
                  isHovered={hoveredPartition === partition.id}
                  setHoveredPartition={setHoveredPartition}
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

/**
 * Partition Chip - Data package being processed
 */
function PartitionChip({ partition, isActive, isCompleted, isHovered, setHoveredPartition }) {
  const sizeClass = partition.size_mb > 100 ? 'fv-partition-large' :
                    partition.size_mb > 50 ? 'fv-partition-medium' : 'fv-partition-small';

  return (
    <div
      className={`fv-partition ${sizeClass} ${isActive ? 'fv-partition-active' : isCompleted ? 'fv-partition-complete' : ''} ${isHovered ? 'fv-partition-hovered' : ''}`}
      onMouseEnter={() => setHoveredPartition(partition.id)}
      onMouseLeave={() => setHoveredPartition(null)}
    >
      <div className="fv-partition-id">P{partition.id}</div>
      {isActive && <div className="fv-partition-pulse"></div>}

      {isHovered && (
        <div className="fv-partition-tooltip">
          <div className="fv-tooltip-header">
            <span>PARTITION {partition.id}</span>
            <span className={`fv-tooltip-status ${isActive ? 'status-active' : isCompleted ? 'status-complete' : 'status-pending'}`}>
              {isActive ? 'RUN' : isCompleted ? 'DONE' : 'WAIT'}
            </span>
          </div>
          <div className="fv-tooltip-row">
            <span>Size</span>
            <span>{partition.size_mb?.toFixed(1) || 0} MB</span>
          </div>
          <div className="fv-tooltip-row">
            <span>Records</span>
            <span>{partition.records_count?.toLocaleString() || 0}</span>
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Live Metrics Panel
 */
function LiveMetricsPanel({ currentState, metrics, currentTime, playbackSpeed }) {
  return (
    <div className="fv-panel">
      <div className="fv-panel-header">
        <span className="fv-panel-icon">◉</span>
        <span className="fv-panel-title">LIVE METRICS</span>
      </div>
      <div className="fv-metrics">
        <div className="fv-metric">
          <div className="fv-metric-label">Playback Speed</div>
          <div className="fv-metric-value">{playbackSpeed.toFixed(1)}x</div>
        </div>
        <div className="fv-metric">
          <div className="fv-metric-label">Active Tasks</div>
          <div className="fv-metric-value fv-metric-active">{currentState?.totalActive || 0}</div>
        </div>
        <div className="fv-metric">
          <div className="fv-metric-label">Completed</div>
          <div className="fv-metric-value fv-metric-complete">{currentState?.totalCompleted || 0}</div>
        </div>
        <div className="fv-metric">
          <div className="fv-metric-label">Shuffles</div>
          <div className="fv-metric-value fv-metric-warning">{metrics.total_shuffles || 0}</div>
        </div>
      </div>
    </div>
  );
}

/**
 * Cluster Health Panel
 */
function ClusterHealthPanel({ nodes, currentState, hoveredExecutor, setHoveredExecutor }) {
  return (
    <div className="fv-panel">
      <div className="fv-panel-header">
        <span className="fv-panel-icon">▦</span>
        <span className="fv-panel-title">CLUSTER HEALTH</span>
      </div>
      <div className="fv-cluster-cards">
        {nodes && nodes.map(node => {
          const tasksByNode = currentState?.tasksByNode?.[node.id] || { active: [], completed: 0 };
          const utilization = node.cores > 0 ? (tasksByNode.active.length / node.cores) * 100 : 0;
          const isHovered = hoveredExecutor === node.id;

          return (
            <div
              key={node.id}
              className={`fv-cluster-card ${isHovered ? 'fv-cluster-card-hovered' : ''}`}
              onMouseEnter={() => setHoveredExecutor(node.id)}
              onMouseLeave={() => setHoveredExecutor(null)}
            >
              <div className="fv-cluster-card-header">
                <span className="fv-cluster-card-name">{node.name}</span>
                <span className="fv-cluster-card-cores">{node.cores}C</span>
              </div>
              <div className="fv-cluster-card-bar">
                <div
                  className="fv-cluster-card-fill"
                  style={{ width: `${utilization}%` }}
                ></div>
              </div>
              <div className="fv-cluster-card-stats">
                <span className="fv-cluster-stat fv-cluster-stat-active">{tasksByNode.active.length}</span>
                <span className="fv-cluster-stat-label">active</span>
                <span className="fv-cluster-stat fv-cluster-stat-complete">{tasksByNode.completed}</span>
                <span className="fv-cluster-stat-label">done</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/**
 * Stage Overview Panel
 */
function StageOverviewPanel({ stages, currentState, currentTime }) {
  return (
    <div className="fv-panel">
      <div className="fv-panel-header">
        <span className="fv-panel-icon">◫</span>
        <span className="fv-panel-title">STAGE OVERVIEW</span>
      </div>
      <div className="fv-stage-list">
        {stages && stages.map(stage => {
          const isActive = currentState?.activeStages?.includes(stage.id);
          const tasks = stage.tasks || [];
          const completed = tasks.filter(t =>
            currentState?.completedTasks?.some(ct => ct.id === t.id)
          ).length;
          const status = completed === tasks.length && tasks.length > 0 ? 'complete' :
                        isActive ? 'active' : 'pending';

          return (
            <div key={stage.id} className={`fv-stage-item fv-stage-item-${status}`}>
              <div className="fv-stage-item-id">S{stage.id}</div>
              <div className="fv-stage-item-info">
                <div className="fv-stage-item-name">{stage.operation_type}</div>
                <div className="fv-stage-item-progress">{completed}/{tasks.length}</div>
              </div>
              <div className={`fv-stage-item-status fv-status-${status}`}>
                {status === 'complete' ? '✓' : status === 'active' ? '◉' : '○'}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/**
 * Calculate execution state at current time
 */
function calculateExecutionState(time, simulationData) {
  const { stages, events, nodes } = simulationData;

  const activeStages = [];
  const activeTasks = [];
  const completedTasks = [];
  const activeShuffles = [];
  const tasksByNode = {};

  nodes?.forEach(node => {
    tasksByNode[node.id] = {
      active: [],
      completed: 0
    };
  });

  events?.forEach(event => {
    if (event.time > time) return;

    switch (event.event_type) {
      case 'stage_start':
        const stage = stages?.find(s => s.id === event.stage_id);
        if (stage && !activeStages.includes(stage.id)) {
          activeStages.push(stage.id);
        }
        break;

      case 'stage_end':
        const idx = activeStages.indexOf(event.stage_id);
        if (idx > -1) {
          activeStages.splice(idx, 1);
        }
        break;

      case 'task_start':
        const startStage = stages?.find(s => s.id === event.stage_id);
        if (startStage) {
          const task = startStage.tasks?.find(t => t.id === event.task_id);
          if (task) {
            activeTasks.push(task);
            if (tasksByNode[task.node_id]) {
              tasksByNode[task.node_id].active.push(task);
            }
          }
        }
        break;

      case 'task_end':
        const endStage = stages?.find(s => s.id === event.stage_id);
        if (endStage) {
          const task = endStage.tasks?.find(t => t.id === event.task_id);
          if (task) {
            const taskIdx = activeTasks.findIndex(t => t.id === task.id);
            if (taskIdx > -1) {
              activeTasks.splice(taskIdx, 1);
            }
            completedTasks.push(task);
            if (tasksByNode[task.node_id]) {
              tasksByNode[task.node_id].completed++;
              const activeIdx = tasksByNode[task.node_id].active.findIndex(t => t.id === task.id);
              if (activeIdx > -1) {
                tasksByNode[task.node_id].active.splice(activeIdx, 1);
              }
            }
          }
        }
        break;

      case 'shuffle_start':
        if (event.details) {
          activeShuffles.push(event.details);
        }
        break;

      case 'shuffle_end':
        const shuffleIdx = activeShuffles.findIndex(
          s => s.from_stage === event.details?.from_stage && s.to_stage === event.details?.to_stage
        );
        if (shuffleIdx > -1) {
          activeShuffles.splice(shuffleIdx, 1);
        }
        break;
    }
  });

  return {
    time,
    activeStages,
    activeTasks,
    completedTasks,
    activeShuffles,
    tasksByNode,
    totalCompleted: completedTasks.length,
    totalActive: activeTasks.length
  };
}

export default FactoryViewRedesigned;
