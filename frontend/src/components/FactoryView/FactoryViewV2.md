# Factory View V2 - SortMergeJoin Shuffle Visualization

## Overview

Factory View V2 is a Sankey-style visualization component that illustrates how Apache Spark executes a **SortMergeJoin** operation. It shows the data flow from source DataFrames through the shuffle/exchange boundary to the final joined result.

---

## Spark Concepts Visualized

### SortMergeJoin Execution Model

When Spark performs a join between two DataFrames on a common key (e.g., `customer_id`), it uses the following process:

```
┌─────────────┐                              ┌─────────────┐
│  Orders DF  │                              │ Customers DF│
│ (8 partitions)                             │(20 partitions)
└──────┬──────┘                              └──────┬──────┘
       │                                            │
       │              ⚡ EXCHANGE                    │
       │         (Shuffle Boundary)                 │
       │                                            │
       ▼                                            ▼
   hash(customer_id) % 200                  hash(customer_id) % 200
       │                                            │
       └────────────────┬───────────────────────────┘
                        │
                        ▼
              ┌─────────────────┐
              │ Shuffle Partitions │
              │   (200 partitions) │
              │                    │
              │ Same keys from both│
              │ sides land in the  │
              │ same partition     │
              └─────────┬─────────┘
                        │
                        ▼
              ┌─────────────────┐
              │   Result DF     │
              │ (Joined Output) │
              └─────────────────┘
```

### Key Concepts

1. **Exchange (Shuffle)**: A wide transformation where data is redistributed across the cluster. Both sides of the join must shuffle their data so that records with the same join key end up in the same partition.

2. **Hash Partitioning**: Spark uses `hash(key) % numPartitions` to determine which partition each record goes to. This ensures co-location of matching keys.

3. **Co-location**: After the shuffle, records from both DataFrames with the same `customer_id` are guaranteed to be in the same partition, enabling a local join.

4. **Data Skew**: When certain keys appear much more frequently than others (e.g., a "guest" account), some partitions receive disproportionately more data, causing performance bottlenecks.

---

## Component Architecture

### Files

```
frontend/src/components/FactoryView/
├── FactoryViewV2.jsx    # Main component
├── FactoryViewV2.css    # Styles
└── FactoryViewV2.md     # This documentation
```

### Data Flow

```javascript
// Node structure: [0] DF_A, [1] DF_B, [2-6] Buckets, [7] Result
const nodes = [
  { name: 'Orders DF', type: 'source', partitions: 8, bytes: 2.4GB },
  { name: 'Customers DF', type: 'source', partitions: 20, bytes: 120MB },
  { name: 'R0-R39', type: 'bucket', partitionCount: 40 },
  { name: 'R40-R79', type: 'bucket', partitionCount: 40, isSkewed: true },
  { name: 'R80-R119', type: 'bucket', partitionCount: 40 },
  { name: 'R120-R159', type: 'bucket', partitionCount: 40 },
  { name: 'R160-R199', type: 'bucket', partitionCount: 40 },
  { name: 'Result DF', type: 'result', partitions: 200 }
];

// Links connect sources → buckets → result
const links = [
  // Orders DF → each bucket (shuffle)
  { source: 0, target: 2, type: 'shuffle', side: 'A' },
  // Customers DF → each bucket (shuffle)
  { source: 1, target: 2, type: 'shuffle', side: 'B' },
  // Buckets → Result (narrow, no shuffle)
  { source: 2, target: 7, type: 'narrow' }
];
```

---

## Implementation Details

### 1. Visual Value Normalization

When one DataFrame is much larger than another (2.4GB vs 120MB), the smaller one would be nearly invisible in the Sankey. We normalize visual values:

```javascript
const maxBytes = Math.max(dfA.bytes, dfB.bytes);
const minVisualValue = maxBytes * 0.30;  // Min 30% of larger
const visualValueA = Math.max(dfA.bytes, minVisualValue);
const visualValueB = Math.max(dfB.bytes, minVisualValue);
```

### 2. Flow Conservation

Sankey diagrams require that flow into a node equals flow out. We use normalized weights that sum to 1:

```javascript
const weights = [1, 3, 1, 0.5, 1];  // Skew simulation
const totalWeight = weights.reduce((sum, w) => sum + w, 0);  // = 6.5
const normalizedWeights = weights.map(w => w / totalWeight);
// [0.154, 0.462, 0.154, 0.077, 0.154] - sums to 1.0
```

This ensures:
- `DF_A → all buckets` = `visualValueA * 1.0` = `visualValueA`
- Links fully connect to nodes without gaps

### 3. Skew Visualization

Bucket 1 (R40-R79) receives 3x weight, simulating a hot key:

```javascript
const weights = [1, 3, 1, 0.5, 1];
//                  ↑ skewed bucket
```

Skewed partitions are:
- Colored red (`#ef4444`) instead of green
- Marked with ⚠ icon
- Highlighted in tooltips

### 4. Exchange Boundary Indicator

A single "⚡ Exchange" badge marks the shuffle boundary:

```jsx
<div className="fv2-shuffle-boundary">
  <div className="fv2-shuffle-line"></div>
  <div className="fv2-shuffle-badge">⚡ Exchange</div>
  <div className="fv2-shuffle-line"></div>
</div>
```

This is positioned at 33% from the left (between source DFs and shuffle partitions).

---

## Custom Recharts Components

### CustomNode

Renders each node with:
- Color based on type (cyan for Orders, purple for Customers, green/red for buckets, cyan-glow for result)
- Glow effect (outer rect with opacity)
- Labels (name + partition count)
- Minimum height enforcement (40px) for readability

```jsx
const CustomNode = ({ x, y, width, height, payload }) => {
  const minHeight = Math.max(height, 40);
  const adjustedY = y - (minHeight - height) / 2;
  // ...render rects and text
};
```

### CustomLink

Renders Bezier curves connecting nodes:
- Color based on link type and side (A=cyan, B=purple)
- Red for skewed links
- Minimum stroke width of 2px

```jsx
const CustomLink = ({ sourceX, targetX, sourceY, targetY, ... }) => {
  return (
    <path
      d={`M${sourceX},${sourceY} C${sourceControlX},${sourceY} ${targetControlX},${targetY} ${targetX},${targetY}`}
      stroke={strokeColor}
      strokeWidth={Math.max(linkWidth, 2)}
    />
  );
};
```

### CustomTooltip

Shows detailed info on hover:
- Link: from/to names, bytes, records, routing formula, % of total
- Node: name, partitions, size, records, skew status

---

## Visual Design

### Color Palette

| Element | Color | Hex |
|---------|-------|-----|
| Orders DF | Cyan | `#06b6d4` |
| Customers DF | Purple | `#8b5cf6` |
| Shuffle Partition | Green | `#10b981` |
| Skewed Partition | Red | `#ef4444` |
| Result DF | Cyan Glow | `#22d3ee` |
| Exchange Badge | Amber | `#fb923c` |
| Background | Deep Space | `#050810` |

### Typography

- Headers: `Orbitron` (display font)
- Data/Code: `Space Mono`, `IBM Plex Mono`

### Effects

- Grid background with pulse animation
- Scanline overlay
- Glow effects on nodes
- Gradient lines for exchange boundary

---

## Usage

```jsx
import FactoryViewV2 from './components/FactoryView/FactoryViewV2';

// With custom data
<FactoryViewV2 shuffleData={myShuffleData} />

// Without data (uses default demo data)
<FactoryViewV2 />
```

---

## JSON Data Schema

The component accepts a `shuffleData` prop with the following structure:

```json
{
  "joinType": "SortMergeJoin",
  "joinKey": "customer_id",
  "shufflePartitions": 200,

  "sources": [
    {
      "id": "orders",
      "name": "Orders DF",
      "partitions": 8,
      "records": 10000000,
      "bytes": 2576980378
    },
    {
      "id": "customers",
      "name": "Customers DF",
      "partitions": 20,
      "records": 500000,
      "bytes": 125829120
    }
  ],

  "shuffleBuckets": [
    {
      "id": "bucket_0",
      "label": "R0-R39",
      "partitionRange": [0, 39],
      "partitionCount": 40,
      "isSkewed": false,
      "contributions": [
        { "sourceId": "orders", "bytes": 396458520, "records": 1538461 },
        { "sourceId": "customers", "bytes": 19358633, "records": 76923 }
      ]
    },
    {
      "id": "bucket_1",
      "label": "R40-R79",
      "partitionRange": [40, 79],
      "partitionCount": 40,
      "isSkewed": true,
      "skewReason": "Hot key: guest_account",
      "contributions": [
        { "sourceId": "orders", "bytes": 1189375560, "records": 4615384 },
        { "sourceId": "customers", "bytes": 58075900, "records": 230769 }
      ]
    }
  ],

  "result": {
    "id": "result",
    "name": "Joined DF",
    "partitions": 200,
    "records": 10500000,
    "bytes": 2702809500
  },

  "metrics": {
    "totalShuffleBytes": 2702809498,
    "skewRatio": 3.0,
    "executionTimeMs": 4200
  }
}
```

### Schema Fields

| Field | Type | Description |
|-------|------|-------------|
| `joinType` | string | Type of join (e.g., "SortMergeJoin", "ShuffleHashJoin") |
| `joinKey` | string | Column name used for join key |
| `shufflePartitions` | number | Total number of shuffle partitions (spark.sql.shuffle.partitions) |
| `sources` | array | Input DataFrames |
| `sources[].id` | string | Unique identifier for the source |
| `sources[].name` | string | Display name |
| `sources[].partitions` | number | Number of input partitions |
| `sources[].records` | number | Total record count |
| `sources[].bytes` | number | Total size in bytes |
| `shuffleBuckets` | array | Grouped shuffle partitions for visualization |
| `shuffleBuckets[].id` | string | Unique identifier |
| `shuffleBuckets[].label` | string | Display label (e.g., "R0-R39") |
| `shuffleBuckets[].partitionRange` | [number, number] | Start and end partition indices |
| `shuffleBuckets[].partitionCount` | number | Number of partitions in this bucket |
| `shuffleBuckets[].isSkewed` | boolean | Whether this bucket has data skew |
| `shuffleBuckets[].skewReason` | string | Optional explanation for skew |
| `shuffleBuckets[].contributions` | array | Data from each source to this bucket |
| `contributions[].sourceId` | string | References `sources[].id` |
| `contributions[].bytes` | number | Bytes from this source to this bucket |
| `contributions[].records` | number | Records from this source to this bucket |
| `result` | object | Output DataFrame |
| `result.name` | string | Display name |
| `result.partitions` | number | Number of output partitions |
| `result.records` | number | Total output records |
| `result.bytes` | number | Total output size |

### Example: 3-Way Join

```json
{
  "joinType": "SortMergeJoin",
  "joinKey": "product_id",
  "shufflePartitions": 100,
  "sources": [
    { "id": "sales", "name": "Sales", "partitions": 16, "records": 5000000, "bytes": 1073741824 },
    { "id": "products", "name": "Products", "partitions": 4, "records": 50000, "bytes": 26214400 },
    { "id": "inventory", "name": "Inventory", "partitions": 8, "records": 100000, "bytes": 52428800 }
  ],
  "shuffleBuckets": [
    {
      "id": "b0", "label": "R0-R24", "partitionRange": [0, 24], "partitionCount": 25,
      "contributions": [
        { "sourceId": "sales", "bytes": 268435456, "records": 1250000 },
        { "sourceId": "products", "bytes": 6553600, "records": 12500 },
        { "sourceId": "inventory", "bytes": 13107200, "records": 25000 }
      ]
    }
  ],
  "result": { "id": "result", "name": "Enriched Sales", "partitions": 100, "records": 4800000, "bytes": 1200000000 }
}
```

---

## Future Enhancements

1. **Real Data Integration**: Parse actual Spark execution metrics from `simulationData`
2. **Animation**: Animate data flow during playback
3. **Multiple Joins**: Support visualizing multiple join operations in sequence
4. **Broadcast Join**: Show broadcast join pattern (small DF replicated to all executors)
5. **Skew Mitigation**: Visualize salting or AQE skew handling

---

## References

- [Spark SQL Join Strategies](https://spark.apache.org/docs/latest/sql-performance-tuning.html)
- [Understanding Shuffles](https://spark.apache.org/docs/latest/rdd-programming-guide.html#shuffle-operations)
- [Recharts Sankey](https://recharts.org/en-US/api/Sankey)
