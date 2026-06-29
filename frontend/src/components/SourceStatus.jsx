import React from 'react';

function StatusDot({ status }) {
  const colors = {
    available: 'var(--success)',
    limited: 'var(--warning)',
    unavailable: 'var(--text-light)',
  };
  return (
    <svg width="8" height="8" viewBox="0 0 8 8">
      <circle cx="4" cy="4" r="4" fill={colors[status] || colors.unavailable} />
    </svg>
  );
}

function SourceStatus({ sources }) {
  if (!sources || sources.length === 0) return null;

  return (
    <div className="source-status-section">
      <p className="source-status-label">Sources searched:</p>
      <div className="source-chips">
        {sources.map((source) => (
          <span
            key={source.name}
            className={`source-chip source-chip-${source.status}`}
            title={source.message || source.status}
          >
            <StatusDot status={source.status} />
            {source.name}
          </span>
        ))}
      </div>
      {/* Show messages for unavailable sources */}
      {sources.some(s => s.status === 'unavailable' && s.message) && (
        <div style={{ marginTop: '0.5rem' }}>
          {sources
            .filter(s => s.status === 'unavailable' && s.message)
            .map(s => (
              <p key={s.name} style={{ fontSize: '0.8rem', color: 'var(--text-light)', margin: '0.15rem 0' }}>
                <strong>{s.name}:</strong> {s.message}
              </p>
            ))}
        </div>
      )}
    </div>
  );
}

export default SourceStatus;
