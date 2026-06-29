import React from 'react';
import JobCard from './JobCard';
import SourceStatus from './SourceStatus';
import EmptyState from './EmptyState';

function DownloadIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
      <polyline points="7 10 12 15 17 10"/>
      <line x1="12" y1="15" x2="12" y2="3"/>
    </svg>
  );
}

function Results({ results, onBack, activeTab, onTabChange, onExportCsv, isExporting }) {
  const {
    strong_matches = [],
    similar_jobs = [],
    sources = [],
    search_expanded,
    message,
    total_fetched,
  } = results;

  const activeJobs = activeTab === 'strong' ? strong_matches : similar_jobs;
  const availableSources = sources.filter((s) => s.status !== 'unavailable').length;
  const totalJobs = strong_matches.length + similar_jobs.length;

  return (
    <div>
      {/* Results header */}
      <div className="results-header">
        <div className="results-header-left">
          <button className="btn btn-secondary" onClick={onBack}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="15 18 9 12 15 6"/>
            </svg>
            New Search
          </button>
          <p className="results-summary">
            <strong>{strong_matches.length}</strong> strong{' '}
            {strong_matches.length === 1 ? 'match' : 'matches'} ·{' '}
            <strong>{similar_jobs.length}</strong> similar{' '}
            {similar_jobs.length === 1 ? 'job' : 'jobs'}
            {availableSources > 0 && (
              <span className="results-summary-sub">
                {' '}from {availableSources} {availableSources === 1 ? 'source' : 'sources'}
                {total_fetched > 0 && ` · ${total_fetched} scanned`}
              </span>
            )}
          </p>
        </div>

        {totalJobs > 0 && (
          <button
            className="btn btn-secondary btn-sm"
            onClick={onExportCsv}
            disabled={isExporting}
            title="Export all results to CSV"
          >
            <DownloadIcon />
            {isExporting ? 'Exporting…' : 'Export CSV'}
          </button>
        )}
      </div>

      {/* Expansion banner */}
      {search_expanded && (
        <div className="info-banner">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
          <span>
            Not enough strong matches — search was expanded to find similar roles.
            See the <strong>Similar Jobs</strong> tab for adjacent opportunities.
          </span>
        </div>
      )}

      {message && !search_expanded && (
        <div className="info-banner info-banner-warn">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
            <line x1="12" y1="9" x2="12" y2="13"/>
            <line x1="12" y1="17" x2="12.01" y2="17"/>
          </svg>
          <span>{message}</span>
        </div>
      )}

      {/* Tab bar */}
      <div className="tab-bar">
        <button
          className={`tab-btn${activeTab === 'strong' ? ' active' : ''}`}
          onClick={() => onTabChange('strong')}
        >
          Strong Matches
          <span className="tab-count">{strong_matches.length}</span>
        </button>
        <button
          className={`tab-btn${activeTab === 'similar' ? ' active' : ''}`}
          onClick={() => onTabChange('similar')}
        >
          Similar Jobs
          <span className="tab-count">{similar_jobs.length}</span>
        </button>
      </div>

      {/* Job list */}
      {activeJobs.length === 0 ? (
        <EmptyState type={activeTab === 'strong' ? 'no-strong-matches' : 'no-jobs'} />
      ) : (
        <div className="job-list">
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
