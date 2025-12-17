import { useState } from 'react';
import './ConceptPanel.css';

/**
 * ConceptPanel - Educational tooltips and explanations for Spark concepts
 */
function ConceptPanel({ currentState, simulationData }) {
  const [expandedConcept, setExpandedConcept] = useState(null);

  const concepts = [
    {
      id: 'partitions',
      title: 'Partitions',
      icon: '🔢',
      summary: 'Data is split into chunks for parallel processing',
      details: `Partitions are the fundamental unit of parallelism in Spark. Your data is divided into ${simulationData?.partition_count || 0} partitions, allowing multiple tasks to process different chunks simultaneously.`,
      tips: [
        'More partitions = more parallelism (up to your core count)',
        'Too many small partitions = overhead',
        'Too few large partitions = underutilized cluster',
        `Optimal: ~2-4 partitions per CPU core (you have ${simulationData?.total_cores || 0} cores)`
      ]
    },
    {
      id: 'stages',
      title: 'Stages',
      icon: '🏭',
      summary: 'Execution is broken into sequential stages',
      details: `Spark divides your job into ${simulationData?.stages?.length || 0} stage(s). A new stage starts whenever data needs to be shuffled between nodes (like in joins or groupBy).`,
      tips: [
        'Fewer stages = faster execution',
        'Stages run sequentially, not in parallel',
        'Shuffles create stage boundaries',
        'Optimize to minimize stage count'
      ]
    },
    {
      id: 'shuffles',
      title: 'Shuffles',
      icon: '🔀',
      summary: 'Expensive data movement across the network',
      details: `Shuffles occur when data needs to be redistributed across partitions (e.g., groupBy, join). Your execution has ${simulationData?.shuffles?.length || 0} shuffle(s).`,
      tips: [
        'Shuffles write data to disk and move it over network',
        'Most expensive operation in Spark',
        'Avoid with broadcast joins for small tables',
        'Use filters before shuffles to reduce data volume'
      ]
    },
    {
      id: 'parallelism',
      title: 'Parallelism',
      icon: '⚡',
      summary: 'Multiple tasks running simultaneously',
      details: `With ${simulationData?.total_cores || 0} CPU cores available, Spark can run ${simulationData?.total_cores || 0} tasks in parallel. Currently ${currentState?.totalActive || 0} tasks are active.`,
      tips: [
        'Parallelism limited by CPU cores',
        `You have ${simulationData?.node_count || 0} nodes × ${simulationData?.cores_per_node || 0} cores = ${simulationData?.total_cores || 0} parallel slots`,
        'More partitions than cores = tasks queue up',
        'Fewer partitions than cores = wasted resources'
      ]
    },
    {
      id: 'broadcast',
      title: 'Broadcast Joins',
      icon: '📡',
      summary: 'Efficient joins for small tables',
      details: 'Instead of shuffling both tables, broadcast the smaller one to all nodes. Each partition of the large table can then join locally.',
      tips: [
        'Use for small tables (< 10MB typically)',
        'Eliminates shuffle on large table',
        'Dramatically faster than shuffle join',
        'Use .broadcast(small_df) to force it'
      ]
    },
    {
      id: 'cache',
      title: 'Caching',
      icon: '💾',
      summary: 'Reuse computed data',
      details: 'When using the same DataFrame multiple times, cache it in memory to avoid recomputing. Especially useful for iterative algorithms.',
      tips: [
        'Use .cache() or .persist() before reusing a DataFrame',
        'Saves time on repeated computations',
        'Uses cluster memory - be mindful of size',
        'Unpersist when done to free memory'
      ]
    }
  ];

  const toggleConcept = (conceptId) => {
    setExpandedConcept(expandedConcept === conceptId ? null : conceptId);
  };

  return (
    <div className="concept-panel">
      <h4 className="concept-panel-title">💡 Learn Spark Concepts</h4>
      <div className="concepts-list">
        {concepts.map(concept => (
          <div
            key={concept.id}
            className={`concept-item ${expandedConcept === concept.id ? 'expanded' : ''}`}
          >
            <button
              className="concept-header"
              onClick={() => toggleConcept(concept.id)}
            >
              <span className="concept-icon">{concept.icon}</span>
              <div className="concept-header-text">
                <div className="concept-title">{concept.title}</div>
                <div className="concept-summary">{concept.summary}</div>
              </div>
              <span className="concept-toggle">
                {expandedConcept === concept.id ? '−' : '+'}
              </span>
            </button>

            {expandedConcept === concept.id && (
              <div className="concept-details">
                <p className="concept-description">{concept.details}</p>
                <div className="concept-tips">
                  <strong>Key Points:</strong>
                  <ul>
                    {concept.tips.map((tip, idx) => (
                      <li key={idx}>{tip}</li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export default ConceptPanel;
