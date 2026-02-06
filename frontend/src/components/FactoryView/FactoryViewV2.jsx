import { useMemo, useState } from 'react';
import { Sankey, Tooltip } from 'recharts';
import './FactoryViewV2.css';
import sampleShuffleData3DF from './sampleShuffleData3DF.json';
import sampleShuffleDataChained from './sampleShuffleDataChained.json';

/**
 * FactoryViewV2 - Multi-Exchange Sankey Visualization
 *
 * Supports spark-sankey/v1 spec with:
 * - Multiple shuffle operations with different keys
 * - Standalone operators (aggregate, distinct, join)
 * - Records as primary thickness metric, bytes in tooltips
 * - View presets for filtering/highlighting stages
 *
 * @param {Object} shuffleData - JSON data in spark-sankey/v1 format
 * @see sampleShuffleDataV2.json for the expected format
 */

// Legacy format for backward compatibility
const DEFAULT_SHUFFLE_DATA = {
  specVersion: 'legacy',
  joinType: 'SortMergeJoin',
  joinKey: 'customer_id',
  shufflePartitions: 200,
  sources: [
    { id: 'orders', name: 'Orders DF', partitions: 8, records: 10000000, bytes: 2576980378 },
    { id: 'customers', name: 'Customers DF', partitions: 20, records: 500000, bytes: 125829120 }
  ],
  shuffleBuckets: [
    {
      id: 'bucket_0', label: 'R0-R39', partitionRange: [0, 39], partitionCount: 40, isSkewed: false,
      contributions: [
        { sourceId: 'orders', bytes: 396458520, records: 1538461 },
        { sourceId: 'customers', bytes: 19358633, records: 76923 }
      ]
    },
    {
      id: 'bucket_1', label: 'R40-R79', partitionRange: [40, 79], partitionCount: 40, isSkewed: true,
      skewReason: 'Hot key: guest_account',
      contributions: [
        { sourceId: 'orders', bytes: 1189375560, records: 4615384 },
        { sourceId: 'customers', bytes: 58075900, records: 230769 }
      ]
    },
    {
      id: 'bucket_2', label: 'R80-R119', partitionRange: [80, 119], partitionCount: 40, isSkewed: false,
      contributions: [
        { sourceId: 'orders', bytes: 396458520, records: 1538461 },
        { sourceId: 'customers', bytes: 19358633, records: 76923 }
      ]
    },
    {
      id: 'bucket_3', label: 'R120-R159', partitionRange: [120, 159], partitionCount: 40, isSkewed: false,
      contributions: [
        { sourceId: 'orders', bytes: 198229260, records: 769230 },
        { sourceId: 'customers', bytes: 9679316, records: 38461 }
      ]
    },
    {
      id: 'bucket_4', label: 'R160-R199', partitionRange: [160, 199], partitionCount: 40, isSkewed: false,
      contributions: [
        { sourceId: 'orders', bytes: 396458520, records: 1538461 },
        { sourceId: 'customers', bytes: 19358633, records: 76923 }
      ]
    }
  ],
  result: { id: 'result', name: 'Joined DF', partitions: 200, records: 10500000, bytes: 2702809500 }
};

// Format helpers
const formatBytes = (bytes) => {
  if (bytes === undefined || bytes === null) return '0 B';
  if (bytes >= 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
  if (bytes >= 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(0)} MB`;
  if (bytes >= 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${bytes} B`;
};

const formatNumber = (num) => {
  if (num === undefined || num === null) return '0';
  if (num >= 1_000_000) return `${(num / 1_000_000).toFixed(1)}M`;
  if (num >= 1_000) return `${(num / 1_000).toFixed(0)}K`;
  return num.toLocaleString();
};

// Color palette for node types
const NODE_COLORS = {
  dataset: { fill: '#06b6d4', glow: 'rgba(6, 182, 212, 0.4)' },      // Cyan
  bucketGroup: { fill: '#10b981', glow: 'rgba(16, 185, 129, 0.4)' }, // Green
  bucketGroupSkewed: { fill: '#ef4444', glow: 'rgba(239, 68, 68, 0.5)' }, // Red
  operator: { fill: '#8b5cf6', glow: 'rgba(139, 92, 246, 0.4)' },    // Purple
  result: { fill: '#22d3ee', glow: 'rgba(34, 211, 238, 0.5)' }       // Cyan glow
};

// Source color palette (for distinguishing multiple input datasets)
const SOURCE_COLORS = [
  { fill: '#06b6d4', glow: 'rgba(6, 182, 212, 0.4)' },   // Cyan
  { fill: '#8b5cf6', glow: 'rgba(139, 92, 246, 0.4)' },  // Purple
  { fill: '#f59e0b', glow: 'rgba(245, 158, 11, 0.4)' },  // Amber
  { fill: '#ec4899', glow: 'rgba(236, 72, 153, 0.4)' },  // Pink
  { fill: '#14b8a6', glow: 'rgba(20, 184, 166, 0.4)' },  // Teal
  { fill: '#f97316', glow: 'rgba(249, 115, 22, 0.4)' },  // Orange
];

/**
 * Parse spark-sankey/v1 spec into Sankey-ready data
 */
const parseSparkSankeySpec = (spec) => {
  const allNodes = spec.nodes || [];
  const links = spec.links || [];
  const stages = spec.stages || [];
  const viewPresets = spec.viewPresets || [];

  // Extract exchange nodes for boundary markers (not part of Sankey)
  const exchanges = allNodes.filter(n => n.type === 'exchange');

  // Filter out exchange nodes from Sankey - they are rendered as boundary markers
  const nodes = allNodes.filter(n => n.type !== 'exchange');

  // Build node index map: id -> sankeyIndex (using filtered nodes)
  const nodeIndexMap = {};
  nodes.forEach((node, idx) => {
    nodeIndexMap[node.id] = idx;
  });

  // Calculate max records for normalization
  const allRecords = nodes
    .filter(n => n.metrics?.records)
    .map(n => n.metrics.records);
  const maxRecords = Math.max(...allRecords, 1);
  const minVisualValue = maxRecords * 0.15; // Min 15% for visibility

  // Normalize visual values based on records
  const visualValues = {};
  nodes.forEach(node => {
    if (node.metrics?.records) {
      visualValues[node.id] = Math.max(node.metrics.records, minVisualValue);
    } else {
      visualValues[node.id] = minVisualValue;
    }
  });

  // Calculate outgoing record totals for each node
  const outgoingTotals = {};
  links.forEach(link => {
    if (!outgoingTotals[link.source]) {
      outgoingTotals[link.source] = 0;
    }
    outgoingTotals[link.source] += link.metrics?.records || 0;
  });

  // Identify input datasets (layer 0) for color assignment
  const inputDatasets = nodes.filter(n => n.type === 'dataset' && n.layer === 0);

  // Build Sankey nodes
  const sankeyNodes = nodes.map((node, idx) => {
    const isSkewed = node.isSkewed || false;
    let colorInfo = NODE_COLORS.dataset;

    if (node.type === 'bucketGroup') {
      colorInfo = isSkewed ? NODE_COLORS.bucketGroupSkewed : NODE_COLORS.bucketGroup;
    } else if (node.type === 'operator') {
      colorInfo = NODE_COLORS.operator;
    } else if (node.type === 'result') {
      colorInfo = NODE_COLORS.result;
    } else if (node.type === 'dataset') {
      // Use source colors for input datasets, default cyan for intermediates
      const sourceIdx = inputDatasets.findIndex(n => n.id === node.id);
      if (sourceIdx >= 0) {
        colorInfo = SOURCE_COLORS[sourceIdx % SOURCE_COLORS.length];
      }
    }

    return {
      ...node,
      name: node.label,
      displayName: node.label,
      sankeyIndex: idx,
      colorInfo,
      isSkewed,
      partitions: node.meta?.partitions,
      partitionRange: node.partitionRange,
      partitionCount: node.partitionCount,
      records: node.metrics?.records,
      bytes: node.metrics?.bytes
    };
  });

  // Build Sankey links with flow conservation via topological propagation.
  //
  // Source nodes (layer 0 datasets) use their normalized visual values.
  // All other nodes inherit their visual value from the sum of incoming
  // link values, ensuring inflow == outflow at every intermediate node.
  // Links are processed layer-by-layer in ascending order.

  // Group links by source layer for topological processing
  const linksBySourceLayer = {};
  links.forEach(link => {
    const sourceNode = nodes[nodeIndexMap[link.source]];
    const layer = sourceNode?.layer ?? 0;
    if (!linksBySourceLayer[layer]) linksBySourceLayer[layer] = [];
    linksBySourceLayer[layer].push(link);
  });

  // Forward propagation: process layers in order
  const propagatedValues = { ...visualValues }; // Start with source visual values
  const computedLinkValues = {}; // link.id -> visual value

  const sortedLayers = Object.keys(linksBySourceLayer).map(Number).sort((a, b) => a - b);
  for (const layer of sortedLayers) {
    const layerLinks = linksBySourceLayer[layer];
    layerLinks.forEach(link => {
      const totalOutgoing = outgoingTotals[link.source] || 1;
      const proportion = (link.metrics?.records || 0) / totalOutgoing;
      const visualValue = propagatedValues[link.source] * proportion;
      computedLinkValues[link.id] = visualValue;

      // Accumulate inflow for target node
      if (!propagatedValues['_inflow_' + link.target]) {
        propagatedValues['_inflow_' + link.target] = 0;
      }
      propagatedValues['_inflow_' + link.target] += visualValue;
    });

    // Update propagated values for targets that have outgoing links
    // (i.e., intermediate nodes, not sinks)
    layerLinks.forEach(link => {
      const targetId = link.target;
      if (outgoingTotals[targetId] > 0) {
        propagatedValues[targetId] = propagatedValues['_inflow_' + targetId];
      }
    });
  }

  // Build final Sankey links using computed values
  const sankeyLinks = links.map(link => {
    const sourceIdx = nodeIndexMap[link.source];
    const targetIdx = nodeIndexMap[link.target];
    const sourceNode = nodes[sourceIdx];
    const targetNode = nodes[targetIdx];
    const visualValue = computedLinkValues[link.id] || 1;

    // Determine if this link is skewed
    const isSkewed = targetNode?.isSkewed || false;

    // Determine link color based on source node
    let sourceColorIdx = 0;
    if (sourceNode?.type === 'dataset') {
      sourceColorIdx = inputDatasets.findIndex(n => n.id === sourceNode.id);
      if (sourceColorIdx < 0) sourceColorIdx = 0;
    }

    return {
      ...link,
      source: sourceIdx,
      target: targetIdx,
      value: Math.max(visualValue, 1), // Ensure minimum visible width
      records: link.metrics?.records || 0,
      bytes: link.metrics?.bytes || 0,
      fromName: sourceNode?.label || link.source,
      toName: targetNode?.label || link.target,
      isSkewed,
      sourceColorIdx,
      routing: link.meta?.routing,
      reason: link.meta?.reason
    };
  });

  // Calculate total metrics (exchanges already extracted above)
  const totalRecords = inputDatasets.reduce((sum, n) => sum + (n.metrics?.records || 0), 0);
  const totalBytes = inputDatasets.reduce((sum, n) => sum + (n.metrics?.bytes || 0), 0);
  const resultNode = nodes.find(n => n.type === 'result');

  return {
    nodes: sankeyNodes,
    links: sankeyLinks,
    stages,
    exchanges,
    viewPresets,
    meta: spec.meta || {},
    metrics: spec.metrics || {},
    totalRecords,
    totalBytes,
    result: resultNode
  };
};

/**
 * Parse legacy shuffle data format (backward compatibility)
 */
const parseLegacyFormat = (data) => {
  const sources = data.sources;
  const buckets = data.shuffleBuckets;
  const result = data.result;
  const joinKey = data.joinKey || 'key';
  const numPartitions = data.shufflePartitions || 200;

  // Create source lookup map
  const sourceMap = {};
  sources.forEach((s, idx) => {
    sourceMap[s.id] = { ...s, index: idx };
  });

  // Calculate total bytes for each source
  const sourceTotals = {};
  sources.forEach(s => {
    sourceTotals[s.id] = buckets.reduce((sum, bucket) => {
      const contrib = bucket.contributions.find(c => c.sourceId === s.id);
      return sum + (contrib?.bytes || 0);
    }, 0);
  });

  // Build nodes
  const numSources = sources.length;
  const numBuckets = buckets.length;

  const nodes = [
    ...sources.map(s => ({
      name: s.name,
      id: s.id,
      displayName: s.name,
      partitions: s.partitions,
      records: s.records,
      bytes: s.bytes,
      type: 'source'
    })),
    ...buckets.map(b => {
      const totalBytes = b.contributions.reduce((sum, c) => sum + c.bytes, 0);
      const totalRecords = b.contributions.reduce((sum, c) => sum + c.records, 0);
      const contribDetails = {};
      b.contributions.forEach(c => {
        contribDetails[c.sourceId] = { bytes: c.bytes, records: c.records };
      });
      return {
        name: b.label,
        id: b.id,
        displayName: b.label,
        partitionRange: b.partitionRange,
        partitionCount: b.partitionCount,
        isSkewed: b.isSkewed || false,
        skewReason: b.skewReason,
        totalBytes,
        totalRecords,
        contributions: contribDetails,
        type: 'bucket'
      };
    }),
    {
      name: result.name,
      id: result.id,
      displayName: result.name,
      partitions: result.partitions,
      records: result.records,
      bytes: result.bytes,
      type: 'result'
    }
  ];

  // Calculate visual values
  const maxSourceBytes = Math.max(...sources.map(s => s.bytes));
  const minVisualValue = maxSourceBytes * 0.30;
  const visualValues = {};
  sources.forEach(s => {
    visualValues[s.id] = Math.max(s.bytes, minVisualValue);
  });

  // Build links
  const links = [];
  const resultNodeIndex = numSources + numBuckets;

  buckets.forEach((bucket, bucketIdx) => {
    const bucketNodeIndex = numSources + bucketIdx;
    bucket.contributions.forEach(contrib => {
      const sourceInfo = sourceMap[contrib.sourceId];
      if (!sourceInfo) return;
      const proportion = contrib.bytes / sourceTotals[contrib.sourceId];
      const visualValue = visualValues[contrib.sourceId] * proportion;
      links.push({
        source: sourceInfo.index,
        target: bucketNodeIndex,
        value: visualValue,
        bytes: contrib.bytes,
        records: contrib.records,
        fromName: sourceInfo.name,
        toName: bucket.label,
        type: 'shuffle',
        side: sourceInfo.index === 0 ? 'A' : 'B',
        isShuffle: true,
        isSkewed: bucket.isSkewed,
        routing: `hash(${joinKey}) % ${numPartitions} → [${bucket.partitionRange[0]}-${bucket.partitionRange[1]}]`,
        percentOfSide: (proportion * 100).toFixed(1)
      });
    });
  });

  buckets.forEach((bucket, bucketIdx) => {
    const bucketNodeIndex = numSources + bucketIdx;
    const bucketNode = nodes[bucketNodeIndex];
    let visualTotal = 0;
    bucket.contributions.forEach(contrib => {
      const proportion = contrib.bytes / sourceTotals[contrib.sourceId];
      visualTotal += visualValues[contrib.sourceId] * proportion;
    });
    links.push({
      source: bucketNodeIndex,
      target: resultNodeIndex,
      value: visualTotal,
      bytes: bucketNode.totalBytes,
      records: bucketNode.totalRecords,
      fromName: bucket.label,
      toName: result.name,
      type: 'narrow',
      isShuffle: false,
      isSkewed: bucket.isSkewed
    });
  });

  const totalShuffleBytes = sources.reduce((sum, s) => sum + s.bytes, 0);

  return {
    nodes,
    links,
    sources,
    joinKey,
    joinType: data.joinType || 'SortMergeJoin',
    numOutputPartitions: numPartitions,
    totalShuffleBytes,
    result,
    isLegacy: true
  };
};

// Helper to convert hex to rgba
const hexToRgba = (hex, alpha) => {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
};

// Custom node component
const CustomNode = ({ x, y, width, height, payload }) => {
  const nodeType = payload.type;
  const isLegacy = payload.isLegacy;

  let fillColor, glowColor;

  if (isLegacy) {
    // Legacy color logic
    if (nodeType === 'source') {
      const colorIdx = (payload.sourceIndex || 0) % SOURCE_COLORS.length;
      fillColor = SOURCE_COLORS[colorIdx].fill;
      glowColor = SOURCE_COLORS[colorIdx].glow;
    } else if (nodeType === 'bucket') {
      fillColor = payload.isSkewed ? '#ef4444' : '#10b981';
      glowColor = payload.isSkewed ? 'rgba(239, 68, 68, 0.5)' : 'rgba(16, 185, 129, 0.4)';
    } else if (nodeType === 'result') {
      fillColor = '#22d3ee';
      glowColor = 'rgba(34, 211, 238, 0.5)';
    } else {
      fillColor = '#06b6d4';
      glowColor = 'rgba(6, 182, 212, 0.4)';
    }
  } else {
    // New spec color logic
    const colorInfo = payload.colorInfo || NODE_COLORS.dataset;
    fillColor = colorInfo.fill;
    glowColor = colorInfo.glow;
  }

  // Extract labels
  let mainLabel = payload.displayName || payload.label || payload.name;
  let subLabel = '';

  if (nodeType === 'dataset' || nodeType === 'source') {
    mainLabel = mainLabel.replace(' DF', '').replace(' DataFrame', '');
    if (mainLabel.length > 14) mainLabel = mainLabel.substring(0, 12) + '..';
    if (payload.partitions) {
      subLabel = `${payload.partitions} partition(s)`;
    }
  } else if (nodeType === 'bucketGroup' || nodeType === 'bucket') {
    if (payload.partitionCount) {
      subLabel = `${payload.partitionCount} partition(s)`;
    }
  } else if (nodeType === 'operator') {
    if (payload.operatorType) {
      subLabel = payload.operatorType;
    }
  } else if (nodeType === 'result') {
    mainLabel = mainLabel.replace(' DF', '').replace(' DataFrame', '');
    if (payload.partitions) {
      subLabel = `${payload.partitions} partition(s)`;
    }
  }

  // Ensure minimum height
  const minHeight = Math.max(height, 40);
  const adjustedY = y - (minHeight - height) / 2;

  // Operator nodes get rounded corners
  const rx = nodeType === 'operator' ? 12 : 6;

  return (
    <g>
      <rect
        x={x - 3}
        y={adjustedY - 3}
        width={width + 6}
        height={minHeight + 6}
        fill={glowColor}
        rx={rx + 2}
        ry={rx + 2}
      />
      <rect
        x={x}
        y={adjustedY}
        width={width}
        height={minHeight}
        fill={fillColor}
        rx={rx}
        ry={rx}
        stroke="#1f2937"
        strokeWidth={2}
      />
      <text
        x={x + width / 2}
        y={adjustedY + minHeight / 2 - (subLabel ? 7 : 0)}
        textAnchor="middle"
        dominantBaseline="middle"
        fill="#050810"
        fontSize={11}
        fontWeight="bold"
        fontFamily="'Space Mono', monospace"
      >
        {mainLabel}
      </text>
      {subLabel && (
        <text
          x={x + width / 2}
          y={adjustedY + minHeight / 2 + 10}
          textAnchor="middle"
          dominantBaseline="middle"
          fill="#050810"
          fontSize={9}
          fontFamily="'IBM Plex Mono', monospace"
          opacity={0.8}
        >
          {subLabel}
        </text>
      )}
      {payload.isSkewed && (
        <text x={x + width + 6} y={adjustedY + 12} fontSize={14} fill="#ef4444">⚠</text>
      )}
    </g>
  );
};

// Custom link component
const CustomLink = ({ sourceX, targetX, sourceY, targetY, sourceControlX, targetControlX, linkWidth, payload }) => {
  let strokeColor = 'rgba(107, 114, 128, 0.5)';

  if (payload.isSkewed) {
    strokeColor = 'rgba(239, 68, 68, 0.6)';
  } else if (payload.type === 'shuffle' || payload.isShuffle) {
    // Use source color
    const colorIdx = (payload.sourceIndex ?? payload.sourceColorIdx ?? (payload.side === 'A' ? 0 : 1)) % SOURCE_COLORS.length;
    const baseColor = SOURCE_COLORS[colorIdx].fill;
    strokeColor = hexToRgba(baseColor, 0.6);
  } else if (payload.type === 'narrow') {
    strokeColor = payload.isSkewed ? 'rgba(239, 68, 68, 0.5)' : 'rgba(34, 211, 238, 0.5)';
  } else {
    // Default - use source color if available
    const colorIdx = (payload.sourceColorIdx ?? 0) % SOURCE_COLORS.length;
    const baseColor = SOURCE_COLORS[colorIdx].fill;
    strokeColor = hexToRgba(baseColor, 0.5);
  }

  return (
    <path
      d={`M${sourceX},${sourceY} C${sourceControlX},${sourceY} ${targetControlX},${targetY} ${targetX},${targetY}`}
      fill="none"
      stroke={strokeColor}
      strokeWidth={Math.max(linkWidth, 4)}
      strokeOpacity={0.85}
    />
  );
};

// Custom tooltip component (records primary, bytes secondary)
const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload || !payload.length) return null;
  const data = payload[0]?.payload;
  if (!data) return null;

  // Link tooltip
  if (data.fromName && data.toName) {
    return (
      <div className="fv2-tooltip">
        <div className="fv2-tooltip-header">
          <span className="fv2-tooltip-route">
            {data.fromName} → {data.toName}
          </span>
        </div>
        <div className="fv2-tooltip-row">
          <span className="fv2-tooltip-label">Records:</span>
          <span className="fv2-tooltip-value fv2-tooltip-primary">{formatNumber(data.records)}</span>
        </div>
        <div className="fv2-tooltip-row">
          <span className="fv2-tooltip-label">Size:</span>
          <span className="fv2-tooltip-value fv2-tooltip-secondary">{formatBytes(data.bytes)}</span>
        </div>
        {data.routing && (
          <div className="fv2-tooltip-row">
            <span className="fv2-tooltip-label">Routing:</span>
            <span className="fv2-tooltip-value fv2-tooltip-code">{data.routing}</span>
          </div>
        )}
        {data.percentOfSide && (
          <div className="fv2-tooltip-row">
            <span className="fv2-tooltip-label">% of total:</span>
            <span className={`fv2-tooltip-value ${data.isSkewed ? 'fv2-tooltip-skew' : ''}`}>
              {data.percentOfSide}% {data.isSkewed && '⚠'}
            </span>
          </div>
        )}
        {data.reason && (
          <div className="fv2-tooltip-note">{data.reason}</div>
        )}
      </div>
    );
  }

  // Node tooltip
  if (data.displayName || data.label) {
    return (
      <div className="fv2-tooltip">
        <div className="fv2-tooltip-header">
          <span className="fv2-tooltip-route">{data.displayName || data.label}</span>
          {data.isSkewed && <span className="fv2-tooltip-badge">SKEWED</span>}
        </div>
        {(data.partitions || data.meta?.partitions) && (
          <div className="fv2-tooltip-row">
            <span className="fv2-tooltip-label">Partitions:</span>
            <span className="fv2-tooltip-value">{data.partitions || data.meta?.partitions}</span>
          </div>
        )}
        {data.partitionRange && (
          <div className="fv2-tooltip-row">
            <span className="fv2-tooltip-label">Range:</span>
            <span className="fv2-tooltip-value">{data.partitionRange[0]} - {data.partitionRange[1]}</span>
          </div>
        )}
        {data.records !== undefined && (
          <div className="fv2-tooltip-row">
            <span className="fv2-tooltip-label">Records:</span>
            <span className="fv2-tooltip-value fv2-tooltip-primary">{formatNumber(data.records)}</span>
          </div>
        )}
        {data.bytes !== undefined && (
          <div className="fv2-tooltip-row">
            <span className="fv2-tooltip-label">Size:</span>
            <span className="fv2-tooltip-value fv2-tooltip-secondary">{formatBytes(data.bytes)}</span>
          </div>
        )}
        {data.operatorType && (
          <div className="fv2-tooltip-row">
            <span className="fv2-tooltip-label">Operator:</span>
            <span className="fv2-tooltip-value">{data.operatorType}</span>
          </div>
        )}
        {data.description && (
          <div className="fv2-tooltip-desc">{data.description}</div>
        )}
        {data.contributions && (
          <>
            {Object.entries(data.contributions).map(([sourceId, contrib]) => (
              <div key={sourceId} className="fv2-tooltip-row">
                <span className="fv2-tooltip-label">From {sourceId}:</span>
                <span className="fv2-tooltip-value">{formatBytes(contrib.bytes)} ({formatNumber(contrib.records)})</span>
              </div>
            ))}
            <div className="fv2-tooltip-row">
              <span className="fv2-tooltip-label">Total:</span>
              <span className="fv2-tooltip-value">{formatBytes(data.totalBytes)}</span>
            </div>
          </>
        )}
        {data.skewReason && (
          <div className="fv2-tooltip-note fv2-tooltip-skew-reason">Cause: {data.skewReason}</div>
        )}
      </div>
    );
  }

  return null;
};

function FactoryViewV2({ shuffleData }) {
  const [activePreset, setActivePreset] = useState('all');

  // Detect format and parse
  const parsedData = useMemo(() => {
    const inputData = shuffleData || sampleShuffleDataChained;

    // Check if it's the new spec format
    if (inputData.specVersion === 'spark-sankey/v1') {
      return parseSparkSankeySpec(inputData);
    }

    // Fall back to legacy format
    return parseLegacyFormat(inputData);
  }, [shuffleData]);

  const isLegacy = parsedData.isLegacy;

  // Apply view preset filtering/highlighting
  const { filteredNodes, filteredLinks, activePresetData } = useMemo(() => {
    if (isLegacy || !parsedData.viewPresets?.length) {
      return {
        filteredNodes: parsedData.nodes,
        filteredLinks: parsedData.links,
        activePresetData: null
      };
    }

    const preset = parsedData.viewPresets.find(p => p.id === activePreset) || parsedData.viewPresets[0];
    if (!preset || preset.id === 'all') {
      return {
        filteredNodes: parsedData.nodes,
        filteredLinks: parsedData.links,
        activePresetData: preset
      };
    }

    // Highlight mode: dim non-matching nodes/links
    const matchingNodeIds = new Set();
    parsedData.nodes.forEach(node => {
      const matchesType = !preset.includeNodeTypes || preset.includeNodeTypes.includes(node.type);
      const matchesStage = !preset.includeStageIds || preset.includeStageIds.includes(node.stageId);
      if (matchesType && matchesStage) {
        matchingNodeIds.add(node.id);
      }
    });

    const highlightedNodes = parsedData.nodes.map(node => ({
      ...node,
      isDimmed: !matchingNodeIds.has(node.id)
    }));

    const highlightedLinks = parsedData.links.map(link => {
      const sourceNode = parsedData.nodes[link.source];
      const targetNode = parsedData.nodes[link.target];
      const isDimmed = !matchingNodeIds.has(sourceNode?.id) && !matchingNodeIds.has(targetNode?.id);
      return { ...link, isDimmed };
    });

    return {
      filteredNodes: highlightedNodes,
      filteredLinks: highlightedLinks,
      activePresetData: preset
    };
  }, [parsedData, activePreset, isLegacy]);

  // Add sourceIndex for legacy format
  const nodesWithIndex = useMemo(() => {
    if (isLegacy) {
      return filteredNodes.map((node, idx) => {
        if (node.type === 'source') {
          const sourceIdx = parsedData.sources.findIndex(s => s.id === node.id);
          return { ...node, sourceIndex: sourceIdx, isLegacy: true };
        }
        return { ...node, isLegacy: true };
      });
    }
    return filteredNodes;
  }, [filteredNodes, parsedData.sources, isLegacy]);

  const linksWithIndex = useMemo(() => {
    if (isLegacy) {
      return filteredLinks.map(link => {
        if (link.type === 'shuffle') {
          const sourceNode = parsedData.nodes[link.source];
          const sourceIdx = parsedData.sources.findIndex(s => s.id === sourceNode?.id);
          return { ...link, sourceIndex: sourceIdx };
        }
        return link;
      });
    }
    return filteredLinks;
  }, [filteredLinks, parsedData.nodes, parsedData.sources, isLegacy]);

  // Extract exchange info for boundary markers
  const exchanges = isLegacy ? [] : (parsedData.exchanges || []);

  // Calculate layer positions for exchange boundaries
  const exchangePositions = useMemo(() => {
    if (!exchanges.length) return [];
    const maxLayer = Math.max(...parsedData.nodes.map(n => n.layer || 0));
    return exchanges.map(ex => ({
      ...ex,
      position: ((ex.layer || 1) / (maxLayer + 1)) * 100
    }));
  }, [exchanges, parsedData.nodes]);

  // Header info
  const title = isLegacy
    ? `${parsedData.joinType?.toUpperCase() || 'SORTMERGEJOIN'} SHUFFLE`
    : (parsedData.meta?.title || 'SPARK EXECUTION');

  const subtitle = isLegacy
    ? `${parsedData.sources?.map(s => `${s.name} (${s.partitions}p)`).join(' ⋈ ')} → ${parsedData.numOutputPartitions} shuffle partitions`
    : (parsedData.meta?.notes || 'Multi-stage pipeline');

  const totalBytes = isLegacy ? parsedData.totalShuffleBytes : parsedData.totalBytes;
  const totalRecords = isLegacy
    ? parsedData.sources?.reduce((sum, s) => sum + s.records, 0)
    : parsedData.totalRecords;
  const resultRecords = parsedData.result?.records || parsedData.result?.metrics?.records;

  return (
    <div className="fv2-container">
      <div className="fv2-grid-bg"></div>
      <div className="fv2-scanline"></div>

      <header className="fv2-header">
        <div className="fv2-header-left">
          <div className="fv2-title-group">
            <div className="fv2-title-icon">⚡</div>
            <div className="fv2-title-text">{title}</div>
          </div>
          <div className="fv2-subtitle">{subtitle}</div>
        </div>
        <div className="fv2-header-stats">
          <div className="fv2-stat">
            <span className="fv2-stat-value">{formatNumber(totalRecords)}</span>
            <span className="fv2-stat-label">Input Records</span>
          </div>
          <div className="fv2-stat">
            <span className="fv2-stat-value">{formatBytes(totalBytes)}</span>
            <span className="fv2-stat-label">Total Data</span>
          </div>
          <div className="fv2-stat">
            <span className="fv2-stat-value">{formatNumber(resultRecords)}</span>
            <span className="fv2-stat-label">Result Records</span>
          </div>
        </div>
      </header>

      {/* View Preset Selector */}
      {!isLegacy && parsedData.viewPresets?.length > 0 && (
        <div className="fv2-preset-selector">
          <span className="fv2-preset-label">VIEW:</span>
          <div className="fv2-preset-buttons">
            {parsedData.viewPresets.map(preset => (
              <button
                key={preset.id}
                className={`fv2-preset-btn ${activePreset === preset.id ? 'active' : ''}`}
                onClick={() => setActivePreset(preset.id)}
                title={preset.description}
              >
                {preset.label}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="fv2-sankey-container">
        <div className="fv2-column-labels">
          {isLegacy ? (
            <>
              <div className="fv2-column-label fv2-label-left">
                <span className="fv2-label-title">Source DataFrames</span>
              </div>
              <div className="fv2-column-label fv2-label-center">
                <span className="fv2-label-title">Shuffle Partitions</span>
              </div>
              <div className="fv2-column-label fv2-label-right">
                <span className="fv2-label-title">Result</span>
              </div>
            </>
          ) : (
            <>
              <div className="fv2-column-label fv2-label-left">
                <span className="fv2-label-title">Input</span>
              </div>
              {parsedData.stages?.map((stage, i) => (
                <div key={stage.id} className="fv2-column-label fv2-label-center">
                  <span className="fv2-label-title">{stage.label}</span>
                </div>
              ))}
              <div className="fv2-column-label fv2-label-right">
                <span className="fv2-label-title">Result</span>
              </div>
            </>
          )}
        </div>

        <div className="fv2-sankey-wrapper">
          {/* Exchange boundary markers */}
          {isLegacy ? (
            <div className="fv2-shuffle-boundary">
              <div className="fv2-shuffle-line"></div>
              <div className="fv2-shuffle-badge">⚡ Exchange</div>
              <div className="fv2-shuffle-line"></div>
            </div>
          ) : (
            exchangePositions.map((ex, i) => (
              <div
                key={ex.id}
                className="fv2-shuffle-boundary"
                style={{ left: `${ex.position}%` }}
              >
                <div className="fv2-shuffle-line"></div>
                <div className="fv2-shuffle-badge">
                  ⚡ hash({ex.keys?.join(', ') || 'key'}) → {ex.shufflePartitions}
                </div>
                <div className="fv2-shuffle-line"></div>
              </div>
            ))
          )}

          <Sankey
            width={1100}
            height={520}
            data={{ nodes: nodesWithIndex, links: linksWithIndex }}
            node={<CustomNode />}
            link={<CustomLink />}
            nodePadding={20}
            nodeWidth={100}
            margin={{ top: 30, right: 50, bottom: 30, left: 50 }}
          >
            <Tooltip content={<CustomTooltip />} />
          </Sankey>
        </div>

        <div className="fv2-info-panel">
          {isLegacy ? (
            <div className="fv2-info-section">
              <div className="fv2-info-title">🔀 {parsedData.joinType} Execution</div>
              <ul className="fv2-info-list">
                <li><strong>⚡ Exchange (Shuffle):</strong> All DataFrames repartitioned by <code>{parsedData.joinKey}</code></li>
                <li><strong>Co-location:</strong> Same keys land in same partition via <code>hash({parsedData.joinKey}) % {parsedData.numOutputPartitions}</code></li>
                <li><strong>Reduce-side join:</strong> Each partition joins co-located records from all sides</li>
              </ul>
            </div>
          ) : (
            <div className="fv2-info-section">
              <div className="fv2-info-title">🔀 Pipeline Overview</div>
              <ul className="fv2-info-list">
                {parsedData.stages?.map(stage => (
                  <li key={stage.id}><strong>{stage.label}:</strong> {stage.description}</li>
                ))}
                {exchanges.map(ex => (
                  <li key={ex.id}><strong>⚡ Exchange:</strong> Shuffle by <code>{ex.keys?.join(', ')}</code> into {ex.shufflePartitions} partitions</li>
                ))}
              </ul>
            </div>
          )}
          {nodesWithIndex.some(n => n.isSkewed) && (
            <div className="fv2-info-section fv2-skew-alert">
              <div className="fv2-info-title">⚠ Skew Detected</div>
              <div className="fv2-skew-details">
                {nodesWithIndex.filter(n => n.isSkewed).map(n => (
                  <span key={n.id || n.sankeyIndex}>
                    <strong>{n.displayName || n.label}</strong> receives disproportionate data.
                    {n.skewReason && <span className="fv2-skew-cause"> Cause: {n.skewReason}</span>}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="fv2-legend">
        <div className="fv2-legend-title">LEGEND</div>
        <div className="fv2-legend-items">
          {isLegacy ? (
            <>
              {parsedData.sources?.map((source, idx) => (
                <div key={source.id} className="fv2-legend-item">
                  <div className="fv2-legend-color" style={{ backgroundColor: SOURCE_COLORS[idx % SOURCE_COLORS.length].fill }}></div>
                  <span className="fv2-legend-label">{source.name}</span>
                </div>
              ))}
            </>
          ) : (
            <>
              <div className="fv2-legend-item">
                <div className="fv2-legend-color" style={{ backgroundColor: NODE_COLORS.dataset.fill }}></div>
                <span className="fv2-legend-label">Dataset</span>
              </div>
              <div className="fv2-legend-item">
                <div className="fv2-legend-color" style={{ backgroundColor: NODE_COLORS.operator.fill }}></div>
                <span className="fv2-legend-label">Operator</span>
              </div>
            </>
          )}
          <div className="fv2-legend-item">
            <div className="fv2-legend-color" style={{ backgroundColor: '#10b981' }}></div>
            <span className="fv2-legend-label">Shuffle Partition</span>
          </div>
          <div className="fv2-legend-item">
            <div className="fv2-legend-color" style={{ backgroundColor: '#ef4444' }}></div>
            <span className="fv2-legend-label">Skewed ⚠</span>
          </div>
          <div className="fv2-legend-item">
            <div className="fv2-legend-color" style={{ backgroundColor: '#22d3ee' }}></div>
            <span className="fv2-legend-label">Result</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default FactoryViewV2;

// Named exports for reuse in SankeyTimelineDashboard
export {
  formatBytes,
  formatNumber,
  NODE_COLORS,
  SOURCE_COLORS,
  hexToRgba,
  parseSparkSankeySpec,
  CustomNode,
  CustomLink,
  CustomTooltip,
};
