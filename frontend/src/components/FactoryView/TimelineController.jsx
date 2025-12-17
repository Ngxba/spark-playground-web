import './TimelineController.css';

/**
 * TimelineController - Playback controls for the execution simulation
 */
function TimelineController({
  currentTime,
  totalDuration,
  isPlaying,
  playbackSpeed,
  onPlay,
  onPause,
  onReset,
  onSpeedChange,
  onSeek,
  events
}) {
  const speedOptions = [0.5, 1, 2, 4];

  const handleScrubberChange = (e) => {
    const newTime = parseFloat(e.target.value);
    onSeek(newTime);
  };

  const formatTime = (seconds) => {
    return `${seconds.toFixed(2)}s`;
  };

  const progress = totalDuration > 0 ? (currentTime / totalDuration) * 100 : 0;

  return (
    <div className="timeline-controller">
      <div className="controls-top">
        {/* Playback Controls */}
        <div className="playback-controls">
          <button
            className="control-btn reset-btn"
            onClick={onReset}
            title="Reset"
          >
            ⏮
          </button>
          {!isPlaying ? (
            <button
              className="control-btn play-btn"
              onClick={onPlay}
              title="Play"
            >
              ▶
            </button>
          ) : (
            <button
              className="control-btn pause-btn"
              onClick={onPause}
              title="Pause"
            >
              ⏸
            </button>
          )}
        </div>

        {/* Speed Control */}
        <div className="speed-control">
          <span className="speed-label">Speed:</span>
          {speedOptions.map(speed => (
            <button
              key={speed}
              className={`speed-btn ${playbackSpeed === speed ? 'active' : ''}`}
              onClick={() => onSpeedChange(speed)}
            >
              {speed}x
            </button>
          ))}
        </div>

        {/* Time Display */}
        <div className="time-display">
          <span className="current-time">{formatTime(currentTime)}</span>
          <span className="time-separator">/</span>
          <span className="total-time">{formatTime(totalDuration)}</span>
        </div>
      </div>

      {/* Timeline Scrubber */}
      <div className="timeline-scrubber">
        <div className="timeline-track">
          {/* Progress bar */}
          <div
            className="timeline-progress"
            style={{ width: `${progress}%` }}
          />

          {/* Event markers */}
          {events && events.map((event, idx) => {
            const position = (event.time / totalDuration) * 100;
            let markerClass = 'timeline-marker';

            if (event.event_type === 'stage_start') {
              markerClass += ' marker-stage';
            } else if (event.event_type === 'shuffle_start') {
              markerClass += ' marker-shuffle';
            }

            return (
              <div
                key={idx}
                className={markerClass}
                style={{ left: `${position}%` }}
                title={`${event.event_type} at ${formatTime(event.time)}`}
              />
            );
          })}

          {/* Scrubber input */}
          <input
            type="range"
            className="timeline-input"
            min="0"
            max={totalDuration}
            step="0.01"
            value={currentTime}
            onChange={handleScrubberChange}
          />
        </div>
      </div>
    </div>
  );
}

export default TimelineController;
