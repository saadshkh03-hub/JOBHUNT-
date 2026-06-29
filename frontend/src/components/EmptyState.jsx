import React from 'react';

const CONFIGS = {
  'no-strong-matches': {
    icon: (
      <svg className="empty-state-icon" viewBox="0 0 64 64" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="32" cy="32" r="28"/>
        <path d="M20 32h24M32 20v24"/>
      </svg>
    ),
    title: 'No strong matches found',
    text: 'We could not find jobs matching your threshold. Try lowering the minimum score, broadening the location, or checking the Similar Jobs tab for adjacent roles.',
  },
  'no-jobs': {
    icon: (
      <svg className="empty-state-icon" viewBox="0 0 64 64" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="8" y="16" width="48" height="36" rx="4"/>
        <path d="M22 16V12a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v4"/>
        <line x1="32" y1="28" x2="32" y2="40"/>
        <line x1="26" y1="34" x2="38" y2="34"/>
      </svg>
    ),
    title: 'No similar jobs found',
    text: 'No additional jobs were found in the expanded search. Try changing your job title, location, or job source filter.',
  },
  'error': {
    icon: (
      <svg className="empty-state-icon" viewBox="0 0 64 64" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="32" cy="32" r="28"/>
        <line x1="32" y1="20" x2="32" y2="36"/>
        <circle cx="32" cy="44" r="2" fill="currentColor"/>
      </svg>
    ),
    title: 'Something went wrong',
    text: 'An error occurred while searching. Make sure the backend is running, then try again.',
  },
};

function EmptyState({ type = 'no-jobs' }) {
  const config = CONFIGS[type] || CONFIGS['no-jobs'];

  return (
    <div className="empty-state">
      {config.icon}
      <h3 className="empty-state-title">{config.title}</h3>
      <p className="empty-state-text">{config.text}</p>
    </div>
  );
}

export default EmptyState;
