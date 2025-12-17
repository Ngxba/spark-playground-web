import { useState, useEffect, useMemo } from 'react';
import DAGVisualization from './DAGVisualization';
import './QueryPlanViewer.css';

function QueryPlanViewer({ dagStructure, physicalPlan, logicalPlan }) {
  const [activeView, setActiveView] = useState('visual');

  // Check if we have any data to display (memoized to prevent recalculation)
  const hasVisualData = useMemo(() => {
    return dagStructure &&
           Array.isArray(dagStructure.nodes) &&
           dagStructure.nodes.length > 0 &&
           Array.isArray(dagStructure.edges);
  }, [dagStructure]);

  const hasPhysicalPlan = useMemo(() => {
    return physicalPlan && physicalPlan.trim().length > 0;
  }, [physicalPlan]);

  const hasLogicalPlan = useMemo(() => {
    return logicalPlan && logicalPlan.trim().length > 0;
  }, [logicalPlan]);

  // Debug logging (only when dagStructure changes)
  useEffect(() => {
    console.log('QueryPlanViewer - dagStructure:', dagStructure);
    console.log('QueryPlanViewer - hasVisualData:', hasVisualData);
    console.log('QueryPlanViewer - nodes:', dagStructure?.nodes);
    console.log('QueryPlanViewer - edges:', dagStructure?.edges);
  }, [dagStructure]);

  if (!hasVisualData && !hasPhysicalPlan && !hasLogicalPlan) {
    return (
      <div className="query-plan-viewer">
        <p className="no-data">No query plan data available. Run your code to see the execution plan.</p>
      </div>
    );
  }

  const formatPlan = (plan) => {
    if (!plan) return 'No plan available';

    // Add syntax highlighting for common Spark operations
    return plan
      .split('\n')
      .map((line, i) => {
        let className = 'plan-line';

        // Highlight different operation types
        if (line.includes('BroadcastHashJoin') || line.includes('Broadcast')) {
          className += ' broadcast-op';
        } else if (line.includes('Exchange') || line.includes('Shuffle')) {
          className += ' shuffle-op';
        } else if (line.includes('Filter') || line.includes('Project')) {
          className += ' filter-op';
        } else if (line.includes('Aggregate') || line.includes('Sort')) {
          className += ' aggregate-op';
        }

        return (
          <div key={i} className={className}>
            {line}
          </div>
        );
      });
  };

  return (
    <div className="query-plan-viewer">
      <div className="plan-view-tabs">
        <button
          className={`plan-tab ${activeView === 'visual' ? 'active' : ''}`}
          onClick={() => setActiveView('visual')}
        >
          Visual DAG
        </button>
        <button
          className={`plan-tab ${activeView === 'physical' ? 'active' : ''}`}
          onClick={() => setActiveView('physical')}
        >
          Physical Plan
        </button>
        <button
          className={`plan-tab ${activeView === 'logical' ? 'active' : ''}`}
          onClick={() => setActiveView('logical')}
        >
          Logical Plan
        </button>
      </div>

      <div className="plan-view-content">
        {activeView === 'visual' && (
          <div className="visual-dag">
            {hasVisualData ? (
              <DAGVisualization
                nodes={dagStructure.nodes}
                edges={dagStructure.edges}
              />
            ) : (
              <div className="no-data-detailed">
                <p>Visual DAG not available</p>
                <p className="hint">Physical plan data: {physicalPlan ? 'Available' : 'Missing'}</p>
                <p className="hint">DAG Structure: {JSON.stringify(dagStructure)}</p>
              </div>
            )}
          </div>
        )}

        {activeView === 'physical' && (
          <div className="plan-text physical-plan">
            <div className="plan-legend">
              <span className="legend-item">
                <span className="legend-color broadcast"></span>
                Broadcast (efficient)
              </span>
              <span className="legend-item">
                <span className="legend-color shuffle"></span>
                Exchange/Shuffle (costly)
              </span>
              <span className="legend-item">
                <span className="legend-color filter"></span>
                Filter/Project (optimized)
              </span>
              <span className="legend-item">
                <span className="legend-color aggregate"></span>
                Aggregate/Sort
              </span>
            </div>
            <pre className="plan-content">
              {hasPhysicalPlan ? formatPlan(physicalPlan) : 'No physical plan available'}
            </pre>
          </div>
        )}

        {activeView === 'logical' && (
          <div className="plan-text logical-plan">
            <pre className="plan-content">
              {hasLogicalPlan ? formatPlan(logicalPlan) : 'No logical plan available'}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}

export default QueryPlanViewer;
