import React, { useState, useEffect } from 'react';

const MESSAGES = [
  'Parsing your resume...',
  'Extracting skills and experience...',
  'Connecting to job sources...',
  'Searching Adzuna...',
  'Searching APS Jobs...',
  'Scoring job matches...',
  'Ranking results by fit...',
  'Almost there...',
];

function LoadingState({ sourcesCount = 3 }) {
  const [msgIndex, setMsgIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setMsgIndex((prev) => (prev + 1) % MESSAGES.length);
    }, 2200);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="loading-state">
      <div className="loading-spinner" role="status" aria-label="Loading" />
      <p className="loading-title">Searching jobs across {sourcesCount} sources</p>
      <p className="loading-subtitle">{MESSAGES[msgIndex]}</p>
    </div>
  );
}

export default LoadingState;
