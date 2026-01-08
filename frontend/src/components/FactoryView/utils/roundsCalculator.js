/**
 * Calculate execution rounds from stage task data
 *
 * This utility analyzes how tasks are scheduled across available cores,
 * grouping them into execution rounds/waves based on their timing.
 *
 * @param {Object} stage - Stage object containing tasks array
 * @param {Array} nodes - Array of node objects with core counts
 * @param {number|null} currentTime - Optional current time for highlighting active round
 * @returns {Object} Rounds analysis data
 */
export function calculateExecutionRounds(stage, nodes, currentTime = null) {
  if (!stage || !stage.tasks || !nodes || nodes.length === 0) {
    return null;
  }

  const tasks = stage.tasks;
  const totalCores = nodes.reduce((sum, node) => sum + node.cores, 0);

  // Calculate total rounds needed
  const totalRounds = Math.ceil(tasks.length / totalCores);

  // Sort tasks by start time
  const sortedTasks = [...tasks].sort((a, b) => a.start_time - b.start_time);

  // Group tasks into rounds based on their execution timing
  const rounds = [];

  sortedTasks.forEach(task => {
    let assignedToRound = false;

    // Try to assign to an existing round
    for (let r = 0; r < rounds.length; r++) {
      const round = rounds[r];

      // Check if this task starts after the round has ended
      // If so, it belongs to a new round
      if (task.start_time >= round.endTime) {
        continue;
      }

      // Check if this task starts during the round and there's capacity
      if (task.start_time >= round.startTime &&
          task.start_time < round.endTime &&
          round.tasks.length < totalCores) {
        // Add task to this round
        round.tasks.push(task);
        round.partitions.push(task.partition_id);
        round.endTime = Math.max(round.endTime, task.end_time);
        round.coreAssignments.push({
          nodeId: task.node_id,
          coreId: task.core_id,
          partitionId: task.partition_id,
          taskId: task.id,
          duration: task.duration
        });
        assignedToRound = true;
        break;
      }
    }

    // Create new round if task wasn't assigned
    if (!assignedToRound) {
      rounds.push({
        roundNumber: rounds.length + 1,
        tasks: [task],
        partitions: [task.partition_id],
        startTime: task.start_time,
        endTime: task.end_time,
        coreAssignments: [{
          nodeId: task.node_id,
          coreId: task.core_id,
          partitionId: task.partition_id,
          taskId: task.id,
          duration: task.duration
        }]
      });
    }
  });

  // Calculate core utilization for each round
  rounds.forEach(round => {
    round.coresUsed = round.tasks.length;
    round.coresIdle = totalCores - round.coresUsed;
    round.utilizationPercent = Math.round((round.coresUsed / totalCores) * 100);
    round.duration = round.endTime - round.startTime;
  });

  // Determine current round based on time
  let currentRound = null;
  if (currentTime !== null) {
    for (let i = 0; i < rounds.length; i++) {
      if (currentTime >= rounds[i].startTime && currentTime < rounds[i].endTime) {
        currentRound = i;
        break;
      }
      // If time is past all rounds, consider the last round as current
      if (i === rounds.length - 1 && currentTime >= rounds[i].endTime) {
        currentRound = i;
      }
    }
  }

  return {
    totalRounds,
    rounds,
    currentRound,
    totalPartitions: tasks.length,
    totalCores,
    stageName: stage.name || 'Stage',
    formula: `${tasks.length} partition${tasks.length !== 1 ? 's' : ''} ÷ ${totalCores} core${totalCores !== 1 ? 's' : ''} = ${totalRounds} round${totalRounds !== 1 ? 's' : ''}`
  };
}

/**
 * Get color class based on utilization percentage
 *
 * @param {number} utilizationPercent - Utilization percentage (0-100)
 * @returns {string} CSS class name for color coding
 */
export function getUtilizationColorClass(utilizationPercent) {
  if (utilizationPercent === 100) return 'utilization-full';
  if (utilizationPercent >= 75) return 'utilization-high';
  if (utilizationPercent >= 50) return 'utilization-medium';
  return 'utilization-low';
}

/**
 * Format time duration for display
 *
 * @param {number} duration - Duration in seconds
 * @returns {string} Formatted duration string
 */
export function formatDuration(duration) {
  if (duration < 1) {
    return `${Math.round(duration * 1000)}ms`;
  }
  return `${duration.toFixed(2)}s`;
}
