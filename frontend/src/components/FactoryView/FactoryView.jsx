import { useState, useEffect } from 'react';
import TimelineController from './TimelineController';
import ClusterView from './ClusterView';
import StageFlow from './StageFlow';
import LiveMetrics from './LiveMetrics';
import ExecutionDiagram from './ExecutionDiagram';
import './FactoryView.css';

/**
 * FactoryView - Live Spark Execution Simulator
 * REDESIGNED: Technical Blueprint Aesthetic
 */
function FactoryView({ simulationData }) {
  const [currentTime, setCurrentTime] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [currentState, setCurrentState] = useState(null);
  const [selectedStageIndex, setSelectedStageIndex] = useState(0);

  // If no simulation data, show message
  if (!simulationData) {
    return (
      <div className="factory-view-empty">
        <div className="empty-state">
          <div className="empty-icon">⚡</div>
          <h3>No Execution Data</h3>
          <p>
            Execute a Spark query to visualize the distributed execution process.
            The factory view will show stages, partitions, tasks, executors, and data flow
            in real-time as your query processes across the cluster.
          </p>
          <div className="empty-features">
            <div className="empty-feature">
              <div className="feature-label">Stage Flow</div>
              <div className="feature-desc">See how stages execute sequentially</div>
            </div>
            <div className="empty-feature">
              <div className="feature-label">Partition Tracking</div>
              <div className="feature-desc">Watch tasks process individual partitions</div>
            </div>
            <div className="empty-feature">
              <div className="feature-label">Executor View</div>
              <div className="feature-desc">Monitor resource utilization</div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const { total_duration, stages, nodes, events, partitions, shuffles, metrics } = simulationData;

  // Auto-play when simulation loads
  useEffect(() => {
    if (simulationData && !isPlaying && currentTime === 0) {
      setIsPlaying(true);
    }
  }, [simulationData]);

  // Calculate current execution state based on currentTime
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

  const handleSeek = (time) => {
    setCurrentTime(time);
  };

  const handleStageSelect = (stageIndex) => {
    setSelectedStageIndex(stageIndex);
    const stage = stages[stageIndex];
    if (stage && events) {
      const stageStartEvent = events.find(
        e => e.event_type === 'stage_start' && e.stage_id === stage.id
      );
      if (stageStartEvent) {
        setCurrentTime(stageStartEvent.time);
        setIsPlaying(false);
      }
    }
  };

  const togglePlayback = () => {
    setIsPlaying(!isPlaying);
  };

  const handleSpeedChange = (speed) => {
    setPlaybackSpeed(speed);
  };

  const handleReset = () => {
    setCurrentTime(0);
    setIsPlaying(false);
  };

  return (
    <div className="factory-view">
      {/* Animated background effect */}
      <div className="factory-bg-animation"></div>

      {/* Header Controls */}
      <div className="factory-header">
        <div className="factory-header-left">
          <div className="factory-title">
            <span className="title-icon">⚡</span>
            <span className="title-text">EXECUTION FACTORY</span>
          </div>
          <div className="factory-subtitle">
            Real-time distributed execution visualization
          </div>
        </div>

        <div className="factory-header-right">
          <div className="playback-controls">
            <button
              className="control-btn control-reset"
              onClick={handleReset}
              title="Reset to start"
            >
              ↺ Reset
            </button>
            <button
              className={`control-btn control-play ${isPlaying ? 'playing' : ''}`}
              onClick={togglePlayback}
            >
              {isPlaying ? '⏸ Pause' : '▶ Play'}
            </button>
            <div className="speed-selector">
              <span className="speed-label">Speed:</span>
              {[0.5, 1, 2, 4].map(speed => (
                <button
                  key={speed}
                  className={`speed-btn ${playbackSpeed === speed ? 'active' : ''}`}
                  onClick={() => handleSpeedChange(speed)}
                >
                  {speed}x
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Timeline */}
      <TimelineController
        currentTime={currentTime}
        totalDuration={total_duration}
        onSeek={handleSeek}
        events={events}
        stages={stages}
        selectedStageIndex={selectedStageIndex}
        onStageSelect={handleStageSelect}
      />

      {/* Main Content Grid */}
      <div className="factory-content">
        {/* Left Column: Execution Diagram */}
        <div className="factory-main">
          <ExecutionDiagram
            simulationData={simulationData}
            currentState={currentState}
            selectedStageIndex={selectedStageIndex}
            onStageSelect={handleStageSelect}
          />
        </div>

        {/* Right Column: Live Metrics & Cluster View */}
        <div className="factory-sidebar">
          <LiveMetrics
            currentState={currentState}
            metrics={metrics}
            partitionCount={partitions?.length || 0}
          />

          <div className="cluster-container">
            <ClusterView
              nodes={nodes}
              currentState={currentState}
              stages={stages}
            />
          </div>

          <div className="stage-flow-container">
            <StageFlow
              stages={stages}
              shuffles={shuffles}
              currentState={currentState}
              selectedStageIndex={selectedStageIndex}
              onStageClick={handleStageSelect}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Calculate the current execution state at a given time
 */
function calculateExecutionState(time, simulationData) {
  const { stages, events, nodes } = simulationData;

  const activeStages = [];
  const activeTasks = [];
  const completedTasks = [];
  const activeShuffles = [];
  const tasksByNode = {};

  nodes.forEach(node => {
    tasksByNode[node.id] = {
      active: [],
      completed: 0
    };
  });

  events.forEach(event => {
    if (event.time > time) return;

    switch (event.event_type) {
      case 'stage_start':
        const stage = stages.find(s => s.id === event.stage_id);
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
        const startStage = stages.find(s => s.id === event.stage_id);
        if (startStage) {
          const task = startStage.tasks.find(t => t.id === event.task_id);
          if (task) {
            activeTasks.push(task);
            if (tasksByNode[task.node_id]) {
              tasksByNode[task.node_id].active.push(task);
            }
          }
        }
        break;

      case 'task_end':
        const endStage = stages.find(s => s.id === event.stage_id);
        if (endStage) {
          const task = endStage.tasks.find(t => t.id === event.task_id);
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
        activeShuffles.push(event.details);
        break;

      case 'shuffle_end':
        const shuffleIdx = activeShuffles.findIndex(
          s => s.from_stage === event.details.from_stage && s.to_stage === event.details.to_stage
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

export default FactoryView;
