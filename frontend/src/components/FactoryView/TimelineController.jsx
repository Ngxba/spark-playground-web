import { useState, useEffect, useMemo } from 'react';
import './TimelineController.css';

/**
 * TimelineController - Timeline visualization for the execution simulation
 */
function TimelineController({
  currentTime,
  totalDuration,
  onSeek,
  events,
  stages,
  selectedStageIndex,
  onStageSelect
}) {
  const [bookmarks, setBookmarks] = useState([]);

  const handleEndMarkerClick = () => {
    if (onSeek && totalDuration > 0) {
      onSeek(totalDuration);
    }
  };

  const formatTime = (seconds) => {
    if (seconds < 60) {
      return `${seconds.toFixed(2)}s`;
    }
    const mins = Math.floor(seconds / 60);
    const secs = (seconds % 60).toFixed(2);
    return `${mins}m ${secs}s`;
  };

  const progress = totalDuration > 0 ? (currentTime / totalDuration) * 100 : 0;

  // Calculate stage segments with proper spacing
  const stageSegments = useMemo(() => {
    if (!stages || !events || stages.length === 0) return [];

    const segments = [];
    for (let i = 0; i < stages.length; i++) {
      const stage = stages[i];
      const stageStartEvent = events.find(
        e => e.event_type === 'stage_start' && e.stage_id === stage.id
      );
      
      // Find stage end (next stage start or total duration)
      let stageEnd = totalDuration;
      if (i < stages.length - 1) {
        const nextStage = stages[i + 1];
        const nextStageStart = events.find(
          e => e.event_type === 'stage_start' && e.stage_id === nextStage.id
        );
        if (nextStageStart) {
          stageEnd = nextStageStart.time;
        }
      }

      if (stageStartEvent) {
        const startPercent = (stageStartEvent.time / totalDuration) * 100;
        const endPercent = (stageEnd / totalDuration) * 100;
        const widthPercent = endPercent - startPercent;

        segments.push({
          stage,
          index: i,
          startTime: stageStartEvent.time,
          endTime: stageEnd,
          startPercent,
          endPercent,
          widthPercent,
          duration: stageEnd - stageStartEvent.time
        });
      }
    }
    return segments;
  }, [stages, events, totalDuration]);

  // Calculate stage marker positions with collision detection
  const stageMarkers = useMemo(() => {
    if (!stageSegments.length) return [];

    const markers = [];
    const minSpacing = 8; // Minimum spacing between markers in percentage

    stageSegments.forEach((segment, idx) => {
      let position = segment.startPercent;
      
      // Check for collisions with previous markers
      if (markers.length > 0) {
        const prevMarker = markers[markers.length - 1];
        const distance = position - prevMarker.position;
        
        if (distance < minSpacing) {
          // Shift this marker to the right
          position = prevMarker.position + minSpacing;
          // But don't go beyond the segment end
          position = Math.min(position, segment.endPercent - 2);
        }
      }

      markers.push({
        ...segment,
        position,
        displayPosition: position
      });
    });

    return markers;
  }, [stageSegments]);

  // Auto-detect key moments for bookmarks
  useEffect(() => {
    if (!events || !stages) return;

    const keyMoments = [];

    // Shuffle bookmarks
    events.forEach(event => {
      if (event.event_type === 'shuffle_start') {
        keyMoments.push({
          time: event.time,
          label: 'Shuffle',
          icon: '🔀',
          type: 'shuffle'
        });
      }
    });

    setBookmarks(keyMoments.sort((a, b) => a.time - b.time));
  }, [events, stages]);

  // Get current stage info
  const currentStage = useMemo(() => {
    if (!stageSegments.length) return null;
    
    for (let i = stageSegments.length - 1; i >= 0; i--) {
      if (currentTime >= stageSegments[i].startTime) {
        return stageSegments[i];
      }
    }
    return stageSegments[0];
  }, [currentTime, stageSegments]);

  return (
    <div className="timeline-controller">
      {/* Time Display */}
      <div className="timeline-header">
        <div className="time-display">
          <span className="time-label">Time:</span>
          <span className="time-value">{formatTime(currentTime)}</span>
          <span className="time-separator">/</span>
          <span className="time-total">{formatTime(totalDuration)}</span>
        </div>
        {currentStage && (
          <div className="current-stage-info">
            <span className="stage-label">Current Stage:</span>
            <span className="stage-name">S{currentStage.stage.id}</span>
          </div>
        )}
      </div>

      {/* Timeline Container */}
      <div className="timeline-scrubber">
        {/* Stage Markers Row */}
        <div className="timeline-markers-row">
          {/* Stage markers with proper spacing */}
          {stageMarkers.map((marker, idx) => (
            <div
              key={marker.stage.id}
              className={`stage-marker ${selectedStageIndex === idx ? 'stage-marker-selected' : ''}`}
              style={{ left: `${marker.displayPosition}%` }}
              onClick={() => onStageSelect && onStageSelect(idx)}
              title={`Stage ${marker.stage.id}: ${marker.stage.name || 'Stage'} (${formatTime(marker.duration)})`}
            >
              <div className="stage-marker-label">
                S{marker.stage.id}
              </div>
            </div>
          ))}

          {/* End marker */}
          <div
            className={`timeline-end-marker ${currentTime >= totalDuration * 0.99 ? 'end-marker-active' : ''}`}
            style={{ left: '100%' }}
            onClick={handleEndMarkerClick}
            title={`End: ${formatTime(totalDuration)}`}
          >
            <div className="end-marker-label">End</div>
          </div>
        </div>

        {/* Timeline Track */}
        <div className="timeline-track-container">
          <div className="timeline-track">
            {/* Stage segments background */}
            {stageSegments.map((segment, idx) => (
              <div
                key={segment.stage.id}
                className={`timeline-segment ${selectedStageIndex === idx ? 'segment-active' : ''} ${idx === selectedStageIndex ? 'segment-selected' : ''}`}
                style={{
                  left: `${segment.startPercent}%`,
                  width: `${segment.widthPercent}%`
                }}
                title={`Stage ${segment.stage.id}: ${formatTime(segment.duration)}`}
              />
            ))}

            {/* Progress bar overlay */}
            <div
              className="timeline-progress"
              style={{ width: `${progress}%` }}
            />

            {/* Stage boundary markers on track */}
            {stageSegments.map((segment, idx) => (
              <div
                key={`boundary-${segment.stage.id}`}
                className={`track-boundary-marker ${selectedStageIndex === idx ? 'boundary-active' : ''}`}
                style={{ left: `${segment.startPercent}%` }}
              />
            ))}

            {/* Shuffle event markers */}
            {events && events.map((event, idx) => {
              if (event.event_type !== 'shuffle_start') return null;
              const position = (event.time / totalDuration) * 100;
              return (
                <div
                  key={`shuffle-${idx}`}
                  className="timeline-marker marker-shuffle"
                  style={{ left: `${position}%` }}
                  title={`Shuffle at ${formatTime(event.time)}`}
                />
              );
            })}
          </div>
        </div>

        {/* Bookmarks Row */}
        {bookmarks.length > 0 && (
          <div className="timeline-bookmarks">
            {bookmarks.map((bookmark, idx) => {
              const position = (bookmark.time / totalDuration) * 100;
              // Only show bookmarks that aren't too close to edges or stage markers
              if (position < 5 || position > 95) return null;
              
              // Check if too close to any stage marker
              const tooClose = stageMarkers.some(m => 
                Math.abs(position - m.displayPosition) < 6
              );
              if (tooClose) return null;

              return (
                <div
                  key={idx}
                  className={`timeline-bookmark bookmark-${bookmark.type}`}
                  style={{ left: `${position}%` }}
                  title={`${bookmark.label} at ${formatTime(bookmark.time)}`}
                >
                  <span className="bookmark-icon">{bookmark.icon}</span>
                  <span className="bookmark-label">{bookmark.label}</span>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

export default TimelineController;
