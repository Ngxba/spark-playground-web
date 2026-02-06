import { useMemo, useState, useCallback, useEffect } from 'react';
import { Sankey, Tooltip } from 'recharts';
import {
  formatBytes,
  formatNumber,
  NODE_COLORS,
  SOURCE_COLORS,
  hexToRgba,
  CustomTooltip,
} from './FactoryViewV2';
import './SankeyTimelineDashboard.css';
import sampleThreeStage from './sampleThreeStage.json';

// --- Parse spark-sankey/v1 spec for staged view ---
function parseStageSpec(spec) {
  const allNodes = spec.nodes || [];
  const links = spec.links || [];
  const stages = spec.stages || [];

  const exchanges = allNodes.filter(n => n.type === 'exchange');
  const nodes = allNodes.filter(n => n.type !== 'exchange');

  return { nodes, links, stages, exchanges, meta: spec.meta || {} };
}

// --- Filter data to a single stage ---
function filterDataByStage(parsed, stageIndex) {
  const stage = parsed.stages[stageIndex];
  if (!stage) return { nodes: [], links: [], exchanges: [], stage: null };
  const stageId = stage.id;

  // Filter nodes belonging to this stage
  const stageNodes = parsed.nodes.filter(n => n.stageId === stageId);
  const nodeIdSet = new Set(stageNodes.map(n => n.id));

  // Filter links where BOTH endpoints are in this stage
  const stageLinks = parsed.links.filter(
    l => nodeIdSet.has(l.source) && nodeIdSet.has(l.target)
  );

  // Build 0-based index map for Recharts Sankey
  const indexMap = {};
  stageNodes.forEach((n, i) => { indexMap[n.id] = i; });

  // Identify input datasets for color assignment
  const inputDatasets = stageNodes.filter(n => n.type === 'dataset' && n.layer === 0);

  // Calculate outgoing totals for proportional sizing
  const outgoingTotals = {};
  stageLinks.forEach(link => {
    if (!outgoingTotals[link.source]) outgoingTotals[link.source] = 0;
    outgoingTotals[link.source] += link.metrics?.records || 0;
  });

  // Build visual values using sqrt scaling
  const sankeyNodes = stageNodes.map((node, idx) => {
    const isSkewed = node.isSkewed || false;
    let colorInfo = NODE_COLORS.dataset;

    if (node.type === 'bucketGroup') {
      colorInfo = isSkewed ? NODE_COLORS.bucketGroupSkewed : NODE_COLORS.bucketGroup;
    } else if (node.type === 'result') {
      colorInfo = NODE_COLORS.result;
    } else if (node.type === 'dataset') {
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
      bytes: node.metrics?.bytes,
    };
  });

  // Build Sankey links with sqrt scaling
  const sankeyLinks = stageLinks.map(link => {
    const sourceIdx = indexMap[link.source];
    const targetIdx = indexMap[link.target];
    const sourceNode = stageNodes[sourceIdx];
    const targetNode = stageNodes[targetIdx];
    const rawRecords = link.metrics?.records || 0;

    // Sqrt scaling for link width
    const scaled = Math.sqrt(rawRecords) * 0.03;
    const value = Math.max(4, Math.min(scaled, 80));

    const isSkewed = targetNode?.isSkewed || false;
    let sourceColorIdx = 0;
    if (sourceNode?.type === 'dataset') {
      sourceColorIdx = inputDatasets.findIndex(n => n.id === sourceNode.id);
      if (sourceColorIdx < 0) sourceColorIdx = 0;
    }

    return {
      ...link,
      source: sourceIdx,
      target: targetIdx,
      value: Math.max(value, 1),
      rawValue: rawRecords,
      records: rawRecords,
      bytes: link.metrics?.bytes || 0,
      fromName: sourceNode?.label || link.source,
      toName: targetNode?.label || link.target,
      isSkewed,
      sourceColorIdx,
      routing: link.meta?.routing,
      reason: link.meta?.reason,
    };
  });

  const stageExchanges = parsed.exchanges.filter(ex => ex.stageId === stageId);

  return { nodes: sankeyNodes, links: sankeyLinks, exchanges: stageExchanges, stage };
}

// --- Compute KPI metrics for a stage ---
function computeStageMetrics(stageView) {
  const stage = stageView.stage;
  if (!stage) return {};
  const m = stage.metrics || {};
  return {
    shuffleRead: m.shuffleReadBytes || 0,
    shuffleWrite: m.shuffleWriteBytes || 0,
    outputPartitions: m.outputPartitions || stage.shufflePartitions || 0,
    skewedBuckets: m.skewedBuckets || 0,
    totalBuckets: m.totalBuckets || 0,
    outputRecords: m.outputRecords || 0,
  };
}

// --- Enhanced CustomNode with onClick for focus mode ---
const FocusableNode = ({ x, y, width, height, payload, onNodeClick, isDimmed }) => {
  const nodeType = payload.type;
  const colorInfo = payload.colorInfo || NODE_COLORS.dataset;
  const fillColor = colorInfo.fill;
  const glowColor = colorInfo.glow;

  let mainLabel = payload.displayName || payload.label || payload.name;
  let subLabel = '';

  if (nodeType === 'dataset') {
    mainLabel = mainLabel.replace(' DF', '').replace(' DataFrame', '');
    if (mainLabel.length > 14) mainLabel = mainLabel.substring(0, 12) + '..';
    if (payload.partitions) subLabel = `${payload.partitions} part.`;
  } else if (nodeType === 'bucketGroup') {
    if (payload.partitionCount) subLabel = `${payload.partitionCount} part.`;
  }

  const minHeight = Math.max(height, 40);
  const adjustedY = y - (minHeight - height) / 2;
  const rx = 6;
  const opacity = isDimmed ? 0.15 : 1;

  return (
    <g
      style={{ cursor: 'pointer', opacity, transition: 'opacity 0.2s ease' }}
      onClick={() => onNodeClick?.(payload)}
    >
      <rect
        x={x - 3} y={adjustedY - 3}
        width={width + 6} height={minHeight + 6}
        fill={glowColor} rx={rx + 2} ry={rx + 2}
      />
      <rect
        x={x} y={adjustedY}
        width={width} height={minHeight}
        fill={fillColor} rx={rx} ry={rx}
        stroke="#1f2937" strokeWidth={2}
      />
      <text
        x={x + width / 2}
        y={adjustedY + minHeight / 2 - (subLabel ? 7 : 0)}
        textAnchor="middle" dominantBaseline="middle"
        fill="#050810" fontSize={11} fontWeight="bold"
        fontFamily="'Space Mono', monospace"
      >
        {mainLabel}
      </text>
      {subLabel && (
        <text
          x={x + width / 2}
          y={adjustedY + minHeight / 2 + 10}
          textAnchor="middle" dominantBaseline="middle"
          fill="#050810" fontSize={9}
          fontFamily="'IBM Plex Mono', monospace"
          opacity={0.8}
        >
          {subLabel}
        </text>
      )}
      {payload.isSkewed && (
        <text x={x + width + 6} y={adjustedY + 12} fontSize={14} fill="#ef4444">
          &#9888;
        </text>
      )}
    </g>
  );
};

// --- Enhanced CustomLink with focus dimming ---
const FocusableLink = ({ sourceX, targetX, sourceY, targetY, sourceControlX, targetControlX, linkWidth, payload, isDimmed }) => {
  let strokeColor = 'rgba(107, 114, 128, 0.5)';

  if (payload.isSkewed) {
    strokeColor = 'rgba(239, 68, 68, 0.6)';
  } else {
    const colorIdx = (payload.sourceColorIdx ?? 0) % SOURCE_COLORS.length;
    const baseColor = SOURCE_COLORS[colorIdx].fill;
    strokeColor = hexToRgba(baseColor, 0.6);
  }

  return (
    <path
      d={`M${sourceX},${sourceY} C${sourceControlX},${sourceY} ${targetControlX},${targetY} ${targetX},${targetY}`}
      fill="none"
      stroke={strokeColor}
      strokeWidth={Math.max(linkWidth, 4)}
      strokeOpacity={isDimmed ? 0.1 : 0.85}
      style={{ transition: 'stroke-opacity 0.2s ease' }}
    />
  );
};

// --- StageKPICards ---
function StageKPICards({ metrics }) {
  const cards = [
    { label: 'Shuffle Read', value: formatBytes(metrics.shuffleRead), icon: '\u2B07' },
    { label: 'Shuffle Write', value: formatBytes(metrics.shuffleWrite), icon: '\u2B06' },
    { label: 'Output Partitions', value: metrics.outputPartitions.toLocaleString(), icon: '\u25A6' },
    {
      label: 'Skew Alert',
      value: metrics.skewedBuckets > 0
        ? `${metrics.skewedBuckets}/${metrics.totalBuckets} skewed`
        : `0/${metrics.totalBuckets} skewed`,
      icon: '\u26A0',
      alert: metrics.skewedBuckets > 0,
    },
    { label: 'Records Out', value: formatNumber(metrics.outputRecords), icon: '\u25B6' },
  ];

  return (
    <div className="std-kpi-row">
      {cards.map((card, i) => (
        <div key={i} className={`std-kpi-card ${card.alert ? 'std-kpi-alert' : ''}`}>
          <div className="std-kpi-icon">{card.icon}</div>
          <div className="std-kpi-value">{card.value}</div>
          <div className="std-kpi-label">{card.label}</div>
        </div>
      ))}
    </div>
  );
}

// --- StageTimelineNav ---
function StageTimelineNav({ stages, currentIndex, onChange, disabled }) {
  return (
    <div className="std-timeline" role="navigation" aria-label="Stage timeline">
      <button
        className="std-timeline-arrow"
        onClick={() => onChange(currentIndex - 1)}
        disabled={disabled || currentIndex === 0}
        aria-label="Previous stage"
      >
        &#8592;
      </button>

      <div className="std-timeline-track">
        {stages.map((stage, i) => {
          const isActive = i === currentIndex;
          const isPast = i < currentIndex;
          return (
            <button
              key={stage.id}
              className={`std-timeline-stop ${isActive ? 'active' : ''} ${isPast ? 'past' : ''}`}
              onClick={() => onChange(i)}
              disabled={disabled}
              aria-label={stage.label}
              aria-current={isActive ? 'step' : undefined}
            >
              <div className="std-timeline-dot" />
              <div className="std-timeline-label">{stage.label}</div>
              <div className="std-timeline-sublabel">
                {stage.joinKey ? `key: ${stage.joinKey}` : ''}
              </div>
            </button>
          );
        })}
        {/* Connecting line */}
        <div className="std-timeline-line" />
        <div
          className="std-timeline-progress"
          style={{ width: `${stages.length > 1 ? (currentIndex / (stages.length - 1)) * 80 : 0}%` }}
        />
      </div>

      <button
        className="std-timeline-arrow"
        onClick={() => onChange(currentIndex + 1)}
        disabled={disabled || currentIndex === stages.length - 1}
        aria-label="Next stage"
      >
        &#8594;
      </button>
    </div>
  );
}

// --- ExchangeBoundary marker ---
function ExchangeBoundary({ exchanges }) {
  if (!exchanges.length) return null;
  const ex = exchanges[0];
  return (
    <div className="std-exchange-boundary">
      <div className="std-exchange-line" />
      <div className="std-exchange-badge">
        &#9889; hash({ex.keys?.join(', ') || 'key'}) &rarr; {ex.shufflePartitions}
      </div>
      <div className="std-exchange-line" />
    </div>
  );
}

// ===========================================
// Main Dashboard Component
// ===========================================
function SankeyTimelineDashboard({ shuffleData, sankeySpec }) {
  const [currentStageIndex, setCurrentStageIndex] = useState(0);
  const [focusedNodeId, setFocusedNodeId] = useState(null);
  const [isTransitioning, setIsTransitioning] = useState(false);

  // Determine data source: real spec > explicit prop > sample fallback
  const hasRealData = !!(sankeySpec || shuffleData);

  // Parse once
  const parsedData = useMemo(() => {
    const input = sankeySpec || shuffleData || sampleThreeStage;
    return parseStageSpec(input);
  }, [sankeySpec, shuffleData]);

  // Filter per stage
  const stageView = useMemo(
    () => filterDataByStage(parsedData, currentStageIndex),
    [parsedData, currentStageIndex]
  );

  // KPI metrics
  const metrics = useMemo(
    () => computeStageMetrics(stageView),
    [stageView]
  );

  // Focused node: which node IDs are "connected"
  const connectedIds = useMemo(() => {
    if (!focusedNodeId) return null;
    const ids = new Set([focusedNodeId]);
    stageView.links.forEach(link => {
      const srcNode = stageView.nodes[link.source];
      const tgtNode = stageView.nodes[link.target];
      if (srcNode?.id === focusedNodeId || tgtNode?.id === focusedNodeId) {
        if (srcNode) ids.add(srcNode.id);
        if (tgtNode) ids.add(tgtNode.id);
      }
    });
    return ids;
  }, [focusedNodeId, stageView]);

  // Stage change handler
  const handleStageChange = useCallback((newIndex) => {
    if (isTransitioning || newIndex === currentStageIndex) return;
    if (newIndex < 0 || newIndex >= parsedData.stages.length) return;
    setIsTransitioning(true);
    setCurrentStageIndex(newIndex);
    setFocusedNodeId(null);
    setTimeout(() => setIsTransitioning(false), 350);
  }, [isTransitioning, currentStageIndex, parsedData.stages.length]);

  // Node click handler
  const handleNodeClick = useCallback((nodePayload) => {
    setFocusedNodeId(prev => prev === nodePayload.id ? null : nodePayload.id);
  }, []);

  // Keyboard navigation
  useEffect(() => {
    const handler = (e) => {
      if (e.key === 'ArrowLeft') {
        handleStageChange(currentStageIndex - 1);
      } else if (e.key === 'ArrowRight') {
        handleStageChange(currentStageIndex + 1);
      } else if (e.key === 'Home') {
        handleStageChange(0);
      } else if (e.key === 'End') {
        handleStageChange(parsedData.stages.length - 1);
      } else if (e.key === 'Escape') {
        setFocusedNodeId(null);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [handleStageChange, currentStageIndex, parsedData.stages.length]);

  const currentStage = parsedData.stages[currentStageIndex];

  // Build nodes/links with focus dimming applied
  const displayNodes = useMemo(() => {
    return stageView.nodes.map(node => ({
      ...node,
      _isDimmed: connectedIds ? !connectedIds.has(node.id) : false,
    }));
  }, [stageView.nodes, connectedIds]);

  const displayLinks = useMemo(() => {
    return stageView.links.map(link => {
      const srcNode = stageView.nodes[link.source];
      const tgtNode = stageView.nodes[link.target];
      const isConnected = connectedIds
        ? connectedIds.has(srcNode?.id) && connectedIds.has(tgtNode?.id)
        : true;
      return { ...link, _isDimmed: !isConnected };
    });
  }, [stageView.links, stageView.nodes, connectedIds]);

  // Custom node renderer that passes focus state
  const renderNode = useCallback((props) => {
    const isDimmed = props.payload._isDimmed;
    return (
      <FocusableNode
        {...props}
        onNodeClick={handleNodeClick}
        isDimmed={isDimmed}
      />
    );
  }, [handleNodeClick]);

  // Custom link renderer that passes focus state
  const renderLink = useCallback((props) => {
    const isDimmed = props.payload._isDimmed;
    return <FocusableLink {...props} isDimmed={isDimmed} />;
  }, []);

  return (
    <div className="std-container">
      <div className="fv2-grid-bg" />
      <div className="fv2-scanline" />

      {/* Sample data banner */}
      {!hasRealData && (
        <div className="std-sample-banner">
          This query has no join operations, so no Sankey pipeline data was generated. Showing a sample pipeline for demonstration. Run a puzzle with joins (e.g. <strong>fast_join</strong>) to see real data here.
        </div>
      )}

      {/* Header */}
      <header className="std-header">
        <div className="std-header-left">
          <div className="std-title-group">
            <div className="std-title-icon">&#9889;</div>
            <div className="std-title-text">STAGE-BY-STAGE PIPELINE</div>
          </div>
          <div className="std-subtitle">
            {parsedData.meta?.title || 'Multi-stage execution'}
          </div>
        </div>
        <div className="std-header-right">
          <div className="std-stage-badge">
            {currentStage?.label || `Stage ${currentStageIndex + 1}`}
          </div>
        </div>
      </header>

      {/* KPI Cards */}
      <StageKPICards metrics={metrics} />

      {/* Sankey View with crossfade */}
      <div className="std-sankey-container" style={{ minHeight: 550 }}>
        <div className="std-column-labels">
          <div className="std-col-label std-col-left">Input</div>
          <div className="std-col-label std-col-center">
            Shuffle Partitions ({currentStage?.shufflePartitions || '?'})
          </div>
          <div className="std-col-label std-col-right">Output</div>
        </div>

        <div className="std-sankey-wrapper" key={currentStageIndex}>
          <ExchangeBoundary exchanges={stageView.exchanges} />

          {stageView.nodes.length > 0 && stageView.links.length > 0 ? (
            <Sankey
              width={1370}
              height={480}
              data={{ nodes: displayNodes, links: displayLinks }}
              node={renderNode}
              link={renderLink}
              nodePadding={30}
              nodeWidth={110}
              margin={{ top: 30, right: 60, bottom: 30, left: 60 }}
            >
              <Tooltip content={<CustomTooltip />} />
            </Sankey>
          ) : (
            <div className="std-empty-stage">No data for this stage</div>
          )}
        </div>

        {/* Focus reset */}
        {focusedNodeId && (
          <button
            className="std-reset-btn"
            onClick={() => setFocusedNodeId(null)}
          >
            Reset Focus
          </button>
        )}
      </div>

      {/* Info Panel */}
      <div className="std-info-panel">
        <div className="std-info-section">
          <div className="std-info-title">
            {currentStage?.label || 'Stage Info'}
          </div>
          <div className="std-info-desc">{currentStage?.description}</div>
          {stageView.exchanges.map(ex => (
            <div key={ex.id} className="std-info-exchange">
              &#9889; Shuffle by <code>{ex.keys?.join(', ')}</code> into {ex.shufflePartitions} partitions
            </div>
          ))}
        </div>
        {stageView.nodes.some(n => n.isSkewed) && (
          <div className="std-info-section std-skew-alert">
            <div className="std-info-title">&#9888; Skew Detected</div>
            {stageView.nodes.filter(n => n.isSkewed).map(n => (
              <div key={n.id} className="std-skew-item">
                <strong>{n.displayName || n.label}</strong> receives disproportionate data.
                {n.skewReason && <span className="std-skew-cause"> Cause: {n.skewReason}</span>}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Timeline Navigation */}
      <StageTimelineNav
        stages={parsedData.stages}
        currentIndex={currentStageIndex}
        onChange={handleStageChange}
        disabled={isTransitioning}
      />

      {/* Legend */}
      <div className="std-legend">
        <div className="std-legend-title">LEGEND</div>
        <div className="std-legend-items">
          {stageView.nodes
            .filter(n => n.type === 'dataset' && n.layer === 0)
            .map((n, i) => (
              <div key={n.id} className="std-legend-item">
                <div className="std-legend-color" style={{ backgroundColor: SOURCE_COLORS[i % SOURCE_COLORS.length].fill }} />
                <span className="std-legend-label">{n.label}</span>
              </div>
            ))}
          <div className="std-legend-item">
            <div className="std-legend-color" style={{ backgroundColor: '#10b981' }} />
            <span className="std-legend-label">Partition Group</span>
          </div>
          <div className="std-legend-item">
            <div className="std-legend-color" style={{ backgroundColor: '#ef4444' }} />
            <span className="std-legend-label">Skewed</span>
          </div>
          <div className="std-legend-item">
            <div className="std-legend-color" style={{ backgroundColor: '#22d3ee' }} />
            <span className="std-legend-label">Output</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default SankeyTimelineDashboard;
