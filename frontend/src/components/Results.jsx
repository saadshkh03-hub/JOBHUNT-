import React from 'react';
import JobCard from './JobCard';
import SourceStatus from './SourceStatus';
import EmptyState from './EmptyState';

function Results({ results, onBack, activeTab, onTabChange }) {
  const { strong_matches = [], similar_jobs = [], sources = [], search_expanded, message, total_fetched } = results;

  const activeJobs = activeTab === 'strong' ? strong_matches : similar_jobs;

  return (
    <div>
      {/* Results header */}
      <div className="results-header">
        <button className="btn btn-secondary" onClick={onBack}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="15 18 9 12 15 6"/>
          </svg>
          Back
        </button>
        <p className="results-summary">
          Found <strong>{strong_matches.length} strong {strong_matches.length === 1 ? 'match' : 'matches'}</strong> and{' '}
          <strong>{similar_jobs.length} similar {similar_jobs.length === 1 ? 'job' : 'jobs'}</strong>
          {sources.length > 0 && ` from ${sources.filter(s => s.status !== 'unavailable').length} ${sources.filter(s => s.status !== 'unavailable').length === 1 ? 'source' : 'sources'}`}
          {total_fetched > 0 && ` (${total_fetched} total scanned)`}
        </p>
      </div>

      {/* Expansion banner */}
      {search_expanded && (
        <div className="info-banner">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
          <span>Search was expanded to find similar roles — see the Similar Jobs tab for adjacent opportunities.</span>
        </div>
      )}

      {/* Custom message */}
      {message && !search_expanded && (
        <div className="info-banner">
          <span>{message}</span>
        </div>
      )}

      {/* Tab bar */}
      <div className="tab-bar">
        <button
          className={`tab-btn${activeTab === 'strong' ? ' active' : ''}`}
          onClick={() => onTabChange('strong')}
        >
          Strong Matches ({strong_matches.length})
        </button>
        <button
          className={`tab-btn${activeTab === 'similar' ? ' active' : ''}`}
          onClick={() => onTabChange('similar')}
        >
          Similar Jobs ({similar_jobs.length})
        </button>
      </div>

      {/* Job list */}
      {activeJobs.length === 0 ? (
        <EmptyState
          type={activeTab === 'strong' ? 'no-strong-matches' : 'no-jobs'}
        />
      ) : (
        <div>
          {activeJobs.map((job) => (
            <JobCard key={job.id} job={job} />
          ))}
        </div>
      )}

      {/* Source status */}
      <SourceStatus sources={sources} />
    </div>
  );
}

export default Results;
