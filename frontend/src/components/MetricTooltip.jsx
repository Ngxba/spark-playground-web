import { useState } from 'react';
import './MetricTooltip.css';

const METRIC_INFO = {
  shuffles: {
    title: 'Shuffles',
    description:
      'A shuffle redistributes data across partitions, requiring data to be written to disk and sent over the network. This happens during operations like join, groupBy, and sort.',
    tips: [
      'Minimize shuffles for better performance',
      'Use broadcast() for small datasets to avoid shuffles',
      'Apply filters before joins to reduce shuffle data size',
    ],
    example: {
      before: 'large_df.join(small_df, "id")',
      after: 'large_df.join(broadcast(small_df), "id")',
      improvement: 'Avoids shuffle by broadcasting small dataset',
    },
  },
  broadcast: {
    title: 'Broadcast Join',
    description:
      'Broadcast sends a copy of a small dataset to all worker nodes, allowing joins without shuffling the large dataset. Ideal for lookup tables under 10MB.',
    tips: [
      'Use for small dimension tables',
      'Automatic for tables < 10MB by default',
      'Can manually trigger with broadcast() function',
    ],
    example: {
      before: 'orders.join(cities, "city_id")',
      after: 'orders.join(broadcast(cities), "city_id")',
      improvement: 'Sends cities table to all nodes once',
    },
  },
  stages: {
    title: 'Stages',
    description:
      'A stage is a set of tasks that can run in parallel without data exchange. Stages are separated by shuffle operations or result collection.',
    tips: [
      'Fewer stages generally mean better performance',
      'Each shuffle creates a new stage boundary',
      'Wide transformations create stage boundaries',
    ],
    example: {
      before: 'df.groupBy("col").count().orderBy("count")',
      after: null,
      improvement: 'This creates 2 stages: groupBy (shuffle) + orderBy (shuffle)',
    },
  },
  cache: {
    title: 'Caching',
    description:
      'Cache stores a DataFrame in memory to avoid recomputation. Essential for iterative algorithms and when the same DataFrame is used multiple times.',
    tips: [
      'Cache DataFrames used multiple times',
      'Unpersist when no longer needed',
      'Choose storage level based on memory availability',
    ],
    example: {
      before: 'df.filter(...)\ndf.count()\ndf.groupBy(...)',
      after: 'cached_df = df.filter(...).cache()\ncached_df.count()\ncached_df.groupBy(...)',
      improvement: 'Reuses filtered data without recomputation',
    },
  },
  skew: {
    title: 'Data Skew',
    description:
      'Data skew occurs when some partitions have significantly more data than others, causing uneven workload distribution and stragglers.',
    tips: [
      'Use salting to distribute hot keys',
      'Repartition to balance data',
      'Consider adaptive query execution (AQE)',
    ],
    example: {
      before: 'df.groupBy("popular_key").count()',
      after: 'df.withColumn("salt", (rand() * 10).cast("int"))\n  .groupBy("popular_key", "salt")\n  .count()',
      improvement: 'Distributes popular key across multiple partitions',
    },
  },
};

function MetricTooltip({ metric, value, children }) {
  const [showTooltip, setShowTooltip] = useState(false);
  const [showExample, setShowExample] = useState(false);

  const info = METRIC_INFO[metric];

  if (!info) {
    return children;
  }

  return (
    <div
      className="metric-tooltip-container"
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      {children}

      {showTooltip && (
        <div className="metric-tooltip">
          <div className="tooltip-header">
            <h4>{info.title}</h4>
            <button
              className="tooltip-close"
              onClick={() => setShowTooltip(false)}
            >
              ×
            </button>
          </div>

          <p className="tooltip-description">{info.description}</p>

          {info.tips && (
            <div className="tooltip-tips">
              <h5>Best Practices:</h5>
              <ul>
                {info.tips.map((tip, i) => (
                  <li key={i}>{tip}</li>
                ))}
              </ul>
            </div>
          )}

          {info.example && (
            <div className="tooltip-example">
              <button
                className="example-toggle"
                onClick={() => setShowExample(!showExample)}
              >
                {showExample ? '▼' : '▶'} Code Example
              </button>

              {showExample && (
                <div className="example-content">
                  {info.example.before && (
                    <div className="example-code">
                      <div className="example-label">Before:</div>
                      <pre>{info.example.before}</pre>
                    </div>
                  )}
                  {info.example.after && (
                    <div className="example-code">
                      <div className="example-label">After:</div>
                      <pre>{info.example.after}</pre>
                    </div>
                  )}
                  <div className="example-improvement">
                    💡 {info.example.improvement}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default MetricTooltip;
