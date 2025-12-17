import { useState } from 'react';
import './ReferencePanel.css';

const SPARK_CONCEPTS = {
  transformations: {
    title: 'Common Transformations',
    icon: '🔄',
    items: [
      {
        name: 'filter(condition)',
        description: 'Returns rows matching the condition',
        example: "df.filter(df['age'] > 21)",
      },
      {
        name: 'select(columns)',
        description: 'Returns specific columns',
        example: "df.select('name', 'age')",
      },
      {
        name: 'groupBy(columns)',
        description: 'Groups data by specified columns',
        example: "df.groupBy('city').count()",
      },
      {
        name: 'join(other_df, on)',
        description: 'Joins two DataFrames',
        example: "df1.join(df2, 'id')",
      },
      {
        name: 'orderBy(columns)',
        description: 'Sorts data by columns',
        example: "df.orderBy('age', ascending=False)",
      },
      {
        name: 'withColumn(name, col)',
        description: 'Adds or replaces a column',
        example: "df.withColumn('double_age', df['age'] * 2)",
      },
    ],
  },
  actions: {
    title: 'Common Actions',
    icon: '⚡',
    items: [
      {
        name: 'show(n)',
        description: 'Displays first n rows (default 20)',
        example: 'df.show(10)',
      },
      {
        name: 'count()',
        description: 'Returns number of rows',
        example: 'df.count()',
      },
      {
        name: 'collect()',
        description: 'Returns all rows as array (use carefully!)',
        example: 'rows = df.collect()',
      },
      {
        name: 'first()',
        description: 'Returns first row',
        example: 'first_row = df.first()',
      },
      {
        name: 'take(n)',
        description: 'Returns first n rows',
        example: 'rows = df.take(5)',
      },
    ],
  },
  optimizations: {
    title: 'Optimization Functions',
    icon: '🚀',
    items: [
      {
        name: 'broadcast(df)',
        description: 'Broadcasts small DataFrame to all workers',
        example: 'large_df.join(broadcast(small_df), "id")',
        tip: 'Use for datasets < 10MB to avoid shuffles',
      },
      {
        name: 'cache()',
        description: 'Caches DataFrame in memory',
        example: 'cached_df = df.filter(...).cache()',
        tip: 'Use when DataFrame is reused multiple times',
      },
      {
        name: 'persist(level)',
        description: 'Persists with custom storage level',
        example: 'df.persist(StorageLevel.MEMORY_AND_DISK)',
        tip: 'More control than cache()',
      },
      {
        name: 'repartition(n)',
        description: 'Redistributes data into n partitions',
        example: 'df.repartition(10)',
        tip: 'Use to balance skewed data',
      },
      {
        name: 'coalesce(n)',
        description: 'Reduces partitions without shuffle',
        example: 'df.coalesce(1)',
        tip: 'Use to reduce partitions efficiently',
      },
    ],
  },
  bestPractices: {
    title: 'Best Practices',
    icon: '💡',
    items: [
      {
        name: 'Minimize Shuffles',
        description: 'Shuffles are expensive - avoid when possible',
        tips: [
          'Use broadcast() for small datasets',
          'Apply filters before joins',
          'Use reduceByKey instead of groupByKey',
        ],
      },
      {
        name: 'Filter Early',
        description: 'Apply filters as early as possible',
        tips: [
          'Filter before join to reduce data size',
          'Use column pruning (select needed columns)',
          'Push filters to data source when possible',
        ],
      },
      {
        name: 'Cache Wisely',
        description: 'Cache intermediate results used multiple times',
        tips: [
          'Cache after expensive transformations',
          'Unpersist when no longer needed',
          'Monitor memory usage',
        ],
      },
      {
        name: 'Partition Appropriately',
        description: 'Balance parallelism and overhead',
        tips: [
          'Default: 200 partitions for shuffles',
          'Rule of thumb: 2-4 partitions per CPU core',
          'Avoid too many small partitions',
        ],
      },
    ],
  },
};

function ReferencePanel() {
  const [isExpanded, setIsExpanded] = useState(false);
  const [activeSection, setActiveSection] = useState('transformations');

  return (
    <div className={`reference-panel ${isExpanded ? 'expanded' : 'collapsed'}`}>
      <button
        className="reference-toggle"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <span className="toggle-icon">{isExpanded ? '◀' : '▶'}</span>
        <span className="toggle-text">Spark Reference</span>
      </button>

      {isExpanded && (
        <div className="reference-content">
          <h3>PySpark Quick Reference</h3>

          <div className="section-tabs">
            {Object.entries(SPARK_CONCEPTS).map(([key, section]) => (
              <button
                key={key}
                className={`section-tab ${activeSection === key ? 'active' : ''}`}
                onClick={() => setActiveSection(key)}
              >
                <span className="section-icon">{section.icon}</span>
                <span className="section-title">{section.title}</span>
              </button>
            ))}
          </div>

          <div className="section-content">
            {activeSection !== 'bestPractices' ? (
              <div className="functions-list">
                {SPARK_CONCEPTS[activeSection].items.map((item, i) => (
                  <div key={i} className="function-card">
                    <div className="function-name">{item.name}</div>
                    <div className="function-description">{item.description}</div>
                    <pre className="function-example">{item.example}</pre>
                    {item.tip && (
                      <div className="function-tip">
                        <strong>💡 Tip:</strong> {item.tip}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="practices-list">
                {SPARK_CONCEPTS.bestPractices.items.map((practice, i) => (
                  <div key={i} className="practice-card">
                    <h4>{practice.name}</h4>
                    <p>{practice.description}</p>
                    <ul>
                      {practice.tips.map((tip, j) => (
                        <li key={j}>{tip}</li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default ReferencePanel;
