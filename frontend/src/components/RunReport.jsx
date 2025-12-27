import { useState } from 'react';
import MetricTooltip from './MetricTooltip';
import ResultsTable from './ResultsTable';
import ExecutionInsights from './ExecutionInsights';
import ProgressiveHints from './ProgressiveHints';
import QueryPlanViewer from './QueryPlanViewer';
import FactoryView from './FactoryView/FactoryView';
import ClusterOverview from './ClusterOverview';
import ConceptPanel from './FactoryView/ConceptPanel';
import './RunReport.css';

function RunReport({ result, onClose }) {
  const [activeTab, setActiveTab] = useState('overview');

  if (!result) return null;

  const renderStars = (count) => {
    return (
      <div className="stars">
        {[...Array(3)].map((_, i) => (
          <span key={i} className={i < count ? 'star-filled' : 'star-empty'}>
            ★
          </span>
        ))}
      </div>
    );
  };

  return (
    <div className="run-report-overlay" onClick={onClose}>
      <div className="run-report-modal" onClick={(e) => e.stopPropagation()}>
        <div className="run-report-header">
          <div className="header-content">
            <h2>Run Report</h2>
            <div className="header-status">
              {result.correct ? (
                <span className="status-badge success">✅ Correct</span>
              ) : (
                <span className="status-badge error">❌ Incorrect</span>
              )}
              {result.correct && renderStars(result.stars)}
            </div>
          </div>
          <button className="close-button" onClick={onClose}>
            ×
          </button>
        </div>

        <div className="report-tabs">
          <button
            className={`report-tab ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            Overview
          </button>
          <button
            className={`report-tab ${activeTab === 'cluster' ? 'active' : ''}`}
            onClick={() => setActiveTab('cluster')}
          >
            🖥️ Cluster
          </button>
          <button
            className={`report-tab ${activeTab === 'factory' ? 'active' : ''}`}
            onClick={() => setActiveTab('factory')}
          >
            Factory View
          </button>
          <button
            className={`report-tab ${activeTab === 'results' ? 'active' : ''}`}
            onClick={() => setActiveTab('results')}
          >
            Results
          </button>
          <button
            className={`report-tab ${activeTab === 'insights' ? 'active' : ''}`}
            onClick={() => setActiveTab('insights')}
          >
            Insights
          </button>
          <button
            className={`report-tab ${activeTab === 'query-plan' ? 'active' : ''}`}
            onClick={() => setActiveTab('query-plan')}
          >
            Query Plan
          </button>
          <button
            className={`report-tab ${activeTab === 'concepts' ? 'active' : ''}`}
            onClick={() => setActiveTab('concepts')}
          >
            💡 Learn Concepts
          </button>
          <button
            className={`report-tab ${activeTab === 'hints' ? 'active' : ''}`}
            onClick={() => setActiveTab('hints')}
          >
            Hints
          </button>
        </div>

        <div className="run-report-content">
          {activeTab === 'overview' && (
            <>
              {/* Error message */}
              {result.error && (
                <div className="report-section error-section">
                  <h4>Error</h4>
                  <pre className="error-text">{result.error}</pre>
                </div>
              )}

              {/* Star Rating */}
              {result.correct && (
                <div className="report-section star-section">
                  <h4>Performance Rating</h4>
                  {renderStars(result.stars)}
                  <p className="star-description">
                    {result.stars === 3 && 'Excellent! Optimal solution.'}
                    {result.stars === 2 && 'Good! Your solution works but could be optimized.'}
                    {result.stars === 1 && 'It works, but there\'s significant room for improvement.'}
                  </p>
                </div>
              )}

              {/* Metrics with Tooltips */}
              {result.metrics && (
                <div className="report-section metrics-section">
                  <h4>Performance Metrics</h4>
                  <div className="metrics-grid">
                    <MetricTooltip metric="shuffles" value={result.metrics.shuffles}>
                      <div className="metric">
                        <span className="metric-label">🔁 Shuffles</span>
                        <span className="metric-value">{result.metrics.shuffles}</span>
                      </div>
                    </MetricTooltip>

                    <MetricTooltip metric="stages" value={result.metrics.stages}>
                      <div className="metric">
                        <span className="metric-label">🏭 Stages</span>
                        <span className="metric-value">{result.metrics.stages}</span>
                      </div>
                    </MetricTooltip>

                    <div className="metric">
                      <span className="metric-label">⏱️ Time</span>
                      <span className="metric-value">
                        {result.metrics.time_simulated}s
                      </span>
                    </div>

                    {result.metrics.broadcast_used && (
                      <MetricTooltip metric="broadcast" value={true}>
                        <div className="metric success-metric">
                          <span className="metric-label">📡 Broadcast</span>
                          <span className="metric-value">Used ✓</span>
                        </div>
                      </MetricTooltip>
                    )}

                    {result.metrics.cache_used && (
                      <MetricTooltip metric="cache" value={true}>
                        <div className="metric success-metric">
                          <span className="metric-label">💾 Cache</span>
                          <span className="metric-value">Used ✓</span>
                        </div>
                      </MetricTooltip>
                    )}

                    {result.metrics.skew_detected && (
                      <MetricTooltip metric="skew" value={true}>
                        <div className="metric warning-metric">
                          <span className="metric-label">⚠️ Skew</span>
                          <span className="metric-value">Detected</span>
                        </div>
                      </MetricTooltip>
                    )}
                  </div>
                </div>
              )}

              {/* Execution Log */}
              {result.execution_log && (
                <div className="report-section log-section">
                  <h4>Execution Log</h4>
                  <pre className="log-text">{result.execution_log}</pre>
                </div>
              )}
            </>
          )}

          {activeTab === 'cluster' && (
            <ClusterOverview
              clusterConfig={result.cluster_config}
            />
          )}

          {activeTab === 'factory' && (
            <FactoryView
              simulationData={result.execution_simulation}
              stageFlowData={result.stage_flow}
            />
          )}

          {activeTab === 'results' && (
            <ResultsTable
              output={result.output}
              expectedOutput={result.expected_output}
              correct={result.correct}
            />
          )}

          {activeTab === 'insights' && (
            <ExecutionInsights
              metrics={result.metrics}
              dagStructure={result.dag_structure}
            />
          )}

          {activeTab === 'query-plan' && (
            <QueryPlanViewer
              dagStructure={result.dag_structure}
              physicalPlan={result.physical_plan}
              logicalPlan={result.logical_plan}
            />
          )}

          {activeTab === 'concepts' && (
            <ConceptPanel
              currentState={null}
              simulationData={result.execution_simulation}
            />
          )}

          {activeTab === 'hints' && (
            <ProgressiveHints
              baseHint={result.hint}
              stars={result.stars}
              metrics={result.metrics}
            />
          )}
        </div>

        <div className="run-report-footer">
          {result.spark_ui_url && (
            <a
              href={result.spark_ui_url}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-spark-ui"
            >
              📊 View This Job in Spark UI
            </a>
          )}
          <button className="btn-primary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

export default RunReport;
