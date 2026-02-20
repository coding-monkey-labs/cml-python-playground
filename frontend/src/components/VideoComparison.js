import React, { useState, useRef, useEffect } from 'react';
import { ButtonGroup, Button, Row, Col } from 'react-bootstrap';
import { FiPlay, FiPause } from 'react-icons/fi';

function VideoComparison({ originalUrl, cleanedUrl }) {
  const [mode, setMode] = useState('side-by-side'); // 'side-by-side' | 'toggle'
  const [showCleaned, setShowCleaned] = useState(false);
  const [playing, setPlaying] = useState(false);
  const originalRef = useRef(null);
  const cleanedRef = useRef(null);

  const togglePlay = () => {
    if (playing) {
      originalRef.current?.pause();
      cleanedRef.current?.pause();
    } else {
      originalRef.current?.play();
      cleanedRef.current?.play();
    }
    setPlaying(!playing);
  };

  // Sync video playback in side-by-side mode
  useEffect(() => {
    const syncVideos = () => {
      if (originalRef.current && cleanedRef.current && mode === 'side-by-side') {
        const diff = Math.abs(originalRef.current.currentTime - cleanedRef.current.currentTime);
        if (diff > 0.5) {
          cleanedRef.current.currentTime = originalRef.current.currentTime;
        }
      }
    };

    const interval = setInterval(syncVideos, 1000);
    return () => clearInterval(interval);
  }, [mode]);

  if (!originalUrl && !cleanedUrl) {
    return <p className="text-muted">No video files available.</p>;
  }

  return (
    <div>
      {/* Controls */}
      <div className="d-flex justify-content-between mb-3">
        <ButtonGroup>
          <Button
            variant={mode === 'side-by-side' ? 'light' : 'outline-light'}
            onClick={() => setMode('side-by-side')}
            size="sm"
          >
            Side by Side
          </Button>
          <Button
            variant={mode === 'toggle' ? 'light' : 'outline-light'}
            onClick={() => setMode('toggle')}
            size="sm"
          >
            Toggle View
          </Button>
        </ButtonGroup>

        <div className="d-flex gap-2 align-items-center">
          {mode === 'toggle' && (
            <ButtonGroup>
              <Button
                variant={!showCleaned ? 'warning' : 'outline-warning'}
                onClick={() => setShowCleaned(false)}
                size="sm"
              >
                Original
              </Button>
              <Button
                variant={showCleaned ? 'success' : 'outline-success'}
                onClick={() => setShowCleaned(true)}
                size="sm"
              >
                Cleaned
              </Button>
            </ButtonGroup>
          )}
          <Button variant="outline-light" onClick={togglePlay} size="sm">
            {playing ? <FiPause /> : <FiPlay />}
          </Button>
        </div>
      </div>

      {/* Video Players */}
      {mode === 'side-by-side' ? (
        <Row>
          <Col md={6}>
            <div className="video-label text-warning mb-1">Original</div>
            <video
              ref={originalRef}
              src={originalUrl}
              controls
              className="w-100 rounded"
              onEnded={() => setPlaying(false)}
            />
          </Col>
          <Col md={6}>
            <div className="video-label text-success mb-1">Cleaned</div>
            <video
              ref={cleanedRef}
              src={cleanedUrl}
              controls
              className="w-100 rounded"
              onEnded={() => setPlaying(false)}
            />
          </Col>
        </Row>
      ) : (
        <div>
          <video
            ref={showCleaned ? cleanedRef : originalRef}
            src={showCleaned ? cleanedUrl : originalUrl}
            controls
            className="w-100 rounded"
            onEnded={() => setPlaying(false)}
          />
        </div>
      )}
    </div>
  );
}

export default VideoComparison;
