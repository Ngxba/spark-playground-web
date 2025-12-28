import { useState, useEffect } from 'react';
import TimelineController from './TimelineController';
import ClusterView from './ClusterView';
import StageFlow from './StageFlow';
import LiveMetrics from './LiveMetrics';
// import ParticleAnimationEngine from './animations/ParticleAnimationEngine'; // DISABLED
import ExecutionDiagram from './ExecutionDiagram';
import './FactoryView.css';

/**
 * FactoryView - Live Spark Execution Simulator
 *
 * Visualizes Spark execution step-by-step showing partitions, stages,
 * shuffles, and parallelism in action.
 */
function FactoryView({ simulationData }) {
  const [currentTime, setCurrentTime] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [currentState, setCurrentState] = useState(null);
  const [partitionPositions, setPartitionPositions] = useState({});
  const [selectedStageIndex, setSelectedStageIndex] = useState(0); // Shared stage selection

  // Debug logging
  console.log('FactoryView - simulationData:', simulationData);

  // If no simulation data, show message
  if (!simulationData) {
    return (
      <div className="factory-view-empty">
        <div className="empty-state">
          <h3>No Execution Simulation Available</h3>
          <p>
            Run your code to see a live visualization of how Spark executes it.
            You'll see partitions flowing through stages, tasks running on nodes,
            and data shuffling across the cluster.
          </p>
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

  // Calculate partition positions for particle animation
  useEffect(() => {
    if (!simulationData) return;

    const positions = {};
    const { partitions, stages } = simulationData;

    // Group partitions by stage
    const partsByStage = {};
    partitions.forEach(p => {
      if (!partsByStage[p.stage_id]) partsByStage[p.stage_id] = [];
      partsByStage[p.stage_id].push(p);
    });

    // Calculate positions
    stages.forEach((stage, stageIdx) => {
      const stageX = 100 + stageIdx * 250;
      const stageParts = partsByStage[stage.id] || [];

      stageParts.forEach((partition, partIdx) => {
        positions[partition.id] = {
          x: stageX + 125,
          y: 150 + partIdx * 40,
        };
      });
    });

    setPartitionPositions(positions);
  }, [simulationData]);

  // Animation loop
  useEffect(() => {
    if (!isPlaying) return;

    const interval = setInterval(() => {
      setCurrentTime((prevTime) => {
        const nextTime = prevTime + (0.016 * playbackSpeed); // 60fps
        if (nextTime >= total_duration) {
          setIsPlaying(false);
          return total_duration;
        }
        return nextTime;
      });
    }, 16); // 60fps

    return () => clearInterval(interval);
  }, [isPlaying, playbackSpeed, total_duration]);

  const handleSeek = (time) => {
    setCurrentTime(time);
  };

  // Handle stage selection - updates both selected stage and seeks to stage start time
  const handleStageSelect = (stageIndex) => {
    setSelectedStageIndex(stageIndex);

    // Find the stage's start time from events
    const stage = stages[stageIndex];
    if (stage && events) {
      const stageStartEvent = events.find(
        e => e.event_type === 'stage_start' && e.stage_id === stage.id
      );
      if (stageStartEvent) {
        setCurrentTime(stageStartEvent.time);
        setIsPlaying(false); // Pause playback when manually selecting a stage
      }
    }
  };

  return (
    <div className="factory-view">
      {/* [A1] Timeline Visualization */}
      <TimelineController
        currentTime={currentTime}
        totalDuration={total_duration}
        onSeek={handleSeek}
        events={events}
        stages={stages}
        selectedStageIndex={selectedStageIndex}
        onStageSelect={handleStageSelect}
      />

      {/* [A2] Detailed Execution Diagram */}
      <ExecutionDiagram
        simulationData={simulationData}
        currentState={currentState}
        selectedStageIndex={selectedStageIndex}
        onStageSelect={handleStageSelect}
      />

      {/* [A3] Main Visualization Area */}
      <div className="factory-canvas" style={{ position: 'relative' }}>
        {/* [A3.1] Cluster View - Shows worker nodes */}
        <ClusterView
          nodes={nodes}
          currentState={currentState}
          stages={stages}
        />

        {/* [A3.2] Stage Flow - Shows stages and their progress */}
        <StageFlow
          stages={stages}
          shuffles={shuffles}
          currentState={currentState}
          selectedStageIndex={selectedStageIndex}
          onStageClick={handleStageSelect}
        />

        {/* [A3.3] Particle Animation Overlay - DISABLED */}
        {/* <ParticleAnimationEngine
          simulationData={simulationData}
          currentTime={currentTime}
          isPlaying={isPlaying}
          playbackSpeed={playbackSpeed}
          partitionPositions={partitionPositions}
        /> */}
      </div>

      {/* [A4] Live Metrics Panel */}
      <LiveMetrics
        currentState={currentState}
        metrics={metrics}
        partitionCount={partitions?.length || 0}
      />
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

  // Initialize task tracking per node
  nodes.forEach(node => {
    tasksByNode[node.id] = {
      active: [],
      completed: 0
    };
  });

  // Process all events up to current time
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
