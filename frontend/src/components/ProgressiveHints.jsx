import { useState } from 'react';
import './ProgressiveHints.css';

function ProgressiveHints({ baseHint, stars, metrics }) {
  const [hintLevel, setHintLevel] = useState(1);

  const generateHints = () => {
    const hints = [];

    // Level 1 - Gentle nudge
    hints.push({
      level: 1,
      type: 'gentle',
      title: 'Initial Feedback',
      content:
        stars === 3
          ? 'Excellent work! Your solution is optimal.'
          : stars === 2
          ? 'Good job! Your solution works but could be optimized.'
          : 'Your solution works, but there are significant optimization opportunities.',
    });

    // Level 2 - Direction
    if (stars < 3) {
      let direction = '';
      if (metrics?.shuffles > 0 && !metrics?.broadcast_used) {
        direction =
          'Consider the size of the datasets you are working with. Are there small datasets that could be handled more efficiently?';
      } else if (metrics?.stages > 3) {
        direction =
          'Your solution creates multiple stages. Think about how to reduce the number of shuffle operations.';
      } else if (!metrics?.cache_used && metrics?.stages > 1) {
        direction =
          'Think about whether any intermediate results are being recomputed unnecessarily.';
      } else {
        direction = baseHint || 'Review Spark best practices for optimization opportunities.';
      }

      hints.push({
        level: 2,
        type: 'direction',
        title: 'Optimization Direction',
        content: direction,
      });
    }

    // Level 3 - Specific suggestion
    if (stars < 3) {
      let suggestion = '';
      if (metrics?.shuffles > 0 && !metrics?.broadcast_used) {
        suggestion =
          'Use the broadcast() function to send small datasets to all workers. This avoids expensive shuffle operations for joins with small lookup tables.';
      } else if (!metrics?.cache_used && metrics?.stages > 1) {
        suggestion =
          'Use .cache() or .persist() on DataFrames that are used multiple times to avoid recomputation.';
      } else if (metrics?.skew_detected) {
        suggestion =
          'Use repartition() or add salt columns to distribute data more evenly across partitions.';
      } else {
        suggestion =
          baseHint || 'Review your transformations to minimize shuffles and maximize parallelism.';
      }

      hints.push({
        level: 3,
        type: 'specific',
        title: 'Specific Suggestion',
        content: suggestion,
      });
    }

    // Level 4 - Code example
    if (stars < 3) {
      let example = null;
      if (metrics?.shuffles > 0 && !metrics?.broadcast_used) {
        example = {
          before: '# Regular join (causes shuffle)\nresult = large_df.join(small_df, "id")',
          after: '# Broadcast join (no shuffle)\nfrom pyspark.sql.functions import broadcast\nresult = large_df.join(broadcast(small_df), "id")',
          explanation:
            'Broadcasting sends the small dataset to all workers once, avoiding the need to shuffle the large dataset.',
        };
      } else if (!metrics?.cache_used) {
        example = {
          before: '# Without caching (recomputes filtered_df)\nfiltered_df = df.filter(...)\ncount = filtered_df.count()\nresult = filtered_df.groupBy(...)',
          after: '# With caching (reuses filtered_df)\nfiltered_df = df.filter(...).cache()\ncount = filtered_df.count()\nresult = filtered_df.groupBy(...)',
          explanation:
            'Caching stores the filtered DataFrame in memory, avoiding recomputation when used multiple times.',
        };
      }

      if (example) {
        hints.push({
          level: 4,
          type: 'example',
          title: 'Code Example',
          content: example,
        });
      }
    }

    return hints;
  };

  const hints = generateHints();
  const currentHint = hints.find((h) => h.level === hintLevel);
  const canShowMore = hintLevel < hints.length;

  const getHintIcon = (type) => {
    switch (type) {
      case 'gentle':
        return '💡';
      case 'direction':
        return '🎯';
      case 'specific':
        return '🔍';
      case 'example':
        return '📝';
      default:
        return '💡';
    }
  };

  return (
    <div className="progressive-hints">
      <div className="hint-level-indicator">
        <div className="level-dots">
          {hints.map((hint, i) => (
            <div
              key={i}
              className={`level-dot ${
                i + 1 <= hintLevel ? 'active' : ''
              } ${i + 1 === hintLevel ? 'current' : ''}`}
              onClick={() => setHintLevel(i + 1)}
            >
              {i + 1}
            </div>
          ))}
        </div>
        <div className="level-label">
          Hint Level {hintLevel} of {hints.length}
        </div>
      </div>

      <div className={`hint-card hint-${currentHint.type}`}>
        <div className="hint-header">
          <span className="hint-icon">{getHintIcon(currentHint.type)}</span>
          <h4>{currentHint.title}</h4>
        </div>

        {currentHint.type !== 'example' ? (
          <p className="hint-content">{currentHint.content}</p>
        ) : (
          <div className="hint-example">
            <div className="example-section">
              <div className="example-label">Before (inefficient):</div>
              <pre className="example-code before">{currentHint.content.before}</pre>
            </div>
            <div className="example-arrow">↓</div>
            <div className="example-section">
              <div className="example-label">After (optimized):</div>
              <pre className="example-code after">{currentHint.content.after}</pre>
            </div>
            <div className="example-explanation">
              <strong>Why this works:</strong> {currentHint.content.explanation}
            </div>
          </div>
        )}

        <div className="hint-actions">
          {hintLevel > 1 && (
            <button
              className="hint-button secondary"
              onClick={() => setHintLevel(hintLevel - 1)}
            >
              ← Previous Hint
            </button>
          )}
          {canShowMore && (
            <button
              className="hint-button primary"
              onClick={() => setHintLevel(hintLevel + 1)}
            >
              {hintLevel === hints.length - 1 ? 'Show Solution' : 'Show More'} →
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default ProgressiveHints;
