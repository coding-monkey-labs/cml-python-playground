import React, { useState, useRef, useEffect } from 'react';
import { Button, ButtonGroup, Card } from 'react-bootstrap';
import { FiPlay, FiPause, FiSkipBack, FiSkipForward } from 'react-icons/fi';

/**
 * Standalone video player with timeline markers.
 * Can be embedded or used for full-screen playback.
 */
function VideoPlayer({ src, markers = [], onTimeUpdate }) {
  const videoRef = useRef(null);
  const [playing, setPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const handleTimeUpdate = () => {
      setCurrentTime(video.currentTime);
      if (onTimeUpdate) onTimeUpdate(video.currentTime);
    };

    const handleLoadedMetadata = () => {
      setDuration(video.duration);
    };

    const handleEnded = () => setPlaying(false);

    video.addEventListener('timeupdate', handleTimeUpdate);
    video.addEventListener('loadedmetadata', handleLoadedMetadata);
    video.addEventListener('ended', handleEnded);

    return () => {
      video.removeEventListener('timeupdate', handleTimeUpdate);
      video.removeEventListener('loadedmetadata', handleLoadedMetadata);
      video.removeEventListener('ended', handleEnded);
    };
  }, [onTimeUpdate]);

  const togglePlay = () => {
    if (playing) {
      videoRef.current?.pause();
    } else {
      videoRef.current?.play();
    }
    setPlaying(!playing);
  };

  const seekTo = (time) => {
    if (videoRef.current) {
      videoRef.current.currentTime = time;
    }
  };

  const skipToMarker = (direction) => {
    const sortedMarkers = [...markers].sort((a, b) => a.time - b.time);
    if (direction === 'forward') {
      const next = sortedMarkers.find(m => m.time > currentTime + 0.5);
      if (next) seekTo(next.time);
    } else {
      const prev = [...sortedMarkers].reverse().find(m => m.time < currentTime - 0.5);
      if (prev) seekTo(prev.time);
    }
  };

  const formatTime = (seconds) => {
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${String(s).padStart(2, '0')}`;
  };

  return (
    <Card bg="dark" text="white">
      <Card.Body className="p-0">
        <video
          ref={videoRef}
          src={src}
          className="w-100 rounded-top"
          style={{ display: 'block' }}
        />

        {/* Timeline with markers */}
        <div className="position-relative mx-3 mt-2" style={{ height: '20px' }}>
          {/* Progress bar */}
          <div
            className="bg-secondary rounded"
            style={{ height: '4px', position: 'absolute', top: '8px', width: '100%', cursor: 'pointer' }}
            onClick={(e) => {
              const rect = e.currentTarget.getBoundingClientRect();
              const pct = (e.clientX - rect.left) / rect.width;
              seekTo(pct * duration);
            }}
          >
            <div
              className="bg-info rounded"
              style={{ height: '100%', width: `${(currentTime / duration) * 100}%` }}
            />
          </div>

          {/* Markers */}
          {markers.map((marker, idx) => (
            <div
              key={idx}
              className={`position-absolute rounded-circle ${
                marker.type === 'remove' ? 'bg-danger' : 'bg-warning'
              }`}
              style={{
                left: `${(marker.time / duration) * 100}%`,
                top: '4px',
                width: '8px',
                height: '8px',
                cursor: 'pointer',
                transform: 'translateX(-4px)',
              }}
              title={marker.label}
              onClick={() => seekTo(marker.time)}
            />
          ))}
        </div>

        {/* Controls */}
        <div className="d-flex justify-content-between align-items-center p-3">
          <small className="text-muted">
            {formatTime(currentTime)} / {formatTime(duration)}
          </small>
          <ButtonGroup size="sm">
            <Button variant="outline-light" onClick={() => skipToMarker('backward')}>
              <FiSkipBack />
            </Button>
            <Button variant="outline-light" onClick={togglePlay}>
              {playing ? <FiPause /> : <FiPlay />}
            </Button>
            <Button variant="outline-light" onClick={() => skipToMarker('forward')}>
              <FiSkipForward />
            </Button>
          </ButtonGroup>
          <div />
        </div>
      </Card.Body>
    </Card>
  );
}

export default VideoPlayer;
