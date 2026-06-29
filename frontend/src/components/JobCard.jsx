import React, { useState } from 'react';
import ScoreBreakdown from './ScoreBreakdown';
import { getAssistance } from '../api';

function getScoreClass(score) {
  if (score >= 70) return 'high';
  if (score >= 50) return 'mid';
  return 'low';
}

function LocationIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
      <circle cx="12" cy="10" r="3"/>
    </svg>
  );
}

function BuildingIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="7" width="20" height="14" rx="2" ry="2"/>
      <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>
    </svg>
  );
}

function WorkTypeIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>
      <line x1="8" y1="21" x2="16" y2="21"/>
      <line x1="12" y1="17" x2="12" y2="21"/>
    </svg>
  );
}

function CalendarIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
      <line x1="16" y1="2" x2="16" y2="6"/>
      <line x1="8" y1="2" x2="8" y2="6"/>
      <line x1="3" y1="10" x2="21" y2="10"/>
    </svg>
  );
}

function ExternalLinkIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
      <polyline points="15 3 21 3 21 9"/>
      <line x1="10" y1="14" x2="21" y2="3"/>
    </svg>
  );
}

function CloseIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <line x1="18" y1="6" x2="6" y2="18"/>
      <line x1="6" y1="6" x2="18" y2="18"/>
    </svg>
  );
}

function formatDate(dateStr) {
  if (!dateStr) return null;
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;
    return d.toLocaleDateString('en-AU', { day: 'numeric', month: 'short', year: 'numeric' });
  } catch {
    return dateStr;
  }
}

function AssistPanel({ job, onClose }) {
  const [activeAction, setActiveAction] = useState(null);
  const [result, setResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const runAssist = async (action) => {
    setActiveAction(action);
    setIsLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await getAssistance({
        action,
        job_title: job.title || '',
        employer: job.employer || '',
        job_description: job.description_snippet || '',
        candidate_summary: '',
        candidate_skills: [],
        candidate_role_families: [],
      });
      setResult(res.content);
    } catch (err) {
      setError('Could not generate content. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="assist-panel">
      <div className="assist-panel-header">
        <span className="assist-panel-title">AI Assist</span>
        <button className="btn-icon" onClick={onClose} title="Close">
          <CloseIcon />
        </button>
      </div>

      <div className="assist-panel-actions">
        <button
          className={`btn btn-secondary btn-sm${activeAction === 'cover_letter' ? ' active' : ''}`}
          onClick={() => runAssist('cover_letter')}
          disabled={isLoading}
        >
          Cover Letter Starter
        </button>
        <button
          className={`btn btn-secondary btn-sm${activeAction === 'tailor_resume' ? ' active' : ''}`}
          onClick={() => runAssist('tailor_resume')}
          disabled={isLoading}
        >
          Resume Tips
        </button>
      </div>

      {isLoading && (
        <div className="assist-loading">
          <div className="spinner-sm" />
          <span>Generating…</span>
        </div>
      )}

      {error && (
        <p className="assist-error">{error}</p>
      )}

      {result && (
        <div className="assist-result">
          <pre className="assist-result-text">{result}</pre>
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => {
              navigator.clipboard?.writeText(result).catch(() => {});
            }}
          >
            Copy to Clipboard
          </button>
        </div>
      )}
    </div>
  );
}

function JobCard({ job }) {
  const [showBreakdown, setShowBreakdown] = useState(false);
  const [showAssist, setShowAssist] = useState(false);
  const scoreClass = getScoreClass(job.score);

  const applyUrl = job.official_url || job.source_url;
  const postedFormatted = formatDate(job.posted_date);
  const closingFormatted = formatDate(job.closing_date);

  return (
    <div className="job-card">
      <div className="job-card-header">
        {/* Score circle */}
        <div className="job-card-score-col">
          <div className={`score-circle score-circle-${scoreClass}`}>
            {Math.round(job.score)}
          </div>
          {job.is_strong_match ? (
            <span className="badge badge-strong">Strong Match</span>
          ) : job.is_similar_job ? (
            <span className="badge badge-similar">Similar</span>
          ) : null}
        </div>

        {/* Main content */}
        <div className="job-card-main">
          <h3 className="job-card-title">{job.title}</h3>

          <div className="job-card-meta">
            {job.employer && (
              <span className="job-card-meta-item">
                <BuildingIcon />
                {job.employer}
              </span>
            )}
            {job.location && (
              <span className="job-card-meta-item">
                <LocationIcon />
                {job.location}
              </span>
            )}
            {job.work_type && (
              <span className="job-card-meta-item">
                <WorkTypeIcon />
                <span style={{ textTransform: 'capitalize' }}>{job.work_type}</span>
              </span>
            )}
            {postedFormatted && (
              <span className="job-card-meta-item">
                <CalendarIcon />
                Posted {postedFormatted}
              </span>
            )}
            {closingFormatted && (
              <span className="job-card-meta-item meta-closing">
                <CalendarIcon />
                Closes {closingFormatted}
              </span>
            )}
          </div>

          {job.salary && (
            <div className="job-card-salary">{job.salary}</div>
          )}

          <div className="job-card-source">
            via {job.source_name}
          </div>
        </div>
      </div>

      {/* Score bar */}
      <div className="score-bar-wrap">
        <div className="score-bar-label">
          <span>Match score</span>
          <strong>{Math.round(job.score)}%</strong>
        </div>
        <div className="score-bar-track">
          <div
            className={`score-bar-fill score-bar-fill-${scoreClass}`}
            style={{ width: `${job.score}%` }}
          />
        </div>
      </div>

      {/* Explanation */}
      {job.explanation && job.explanation.length > 0 && (
        <ul className="explanation-list">
          {job.explanation.map((item, i) => (
            <li key={i} className="explanation-item explanation-positive">
              <svg className="icon-check" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
              {item}
            </li>
          ))}
        </ul>
      )}

      {/* Blockers */}
      {job.blockers && job.blockers.length > 0 && (
        <ul className="explanation-list" style={{ marginTop: '0.35rem' }}>
          {job.blockers.map((b, i) => (
            <li key={i} className="explanation-item explanation-blocker">
              <svg className="icon-warn" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                <line x1="12" y1="9" x2="12" y2="13"/>
                <line x1="12" y1="17" x2="12.01" y2="17"/>
              </svg>
              {b}
            </li>
          ))}
        </ul>
      )}

      {/* Missing skills */}
      {job.missing_skills && job.missing_skills.length > 0 && (
        <div className="missing-skills-wrap">
          <span className="missing-skills-label">Skills to develop: </span>
          <div className="missing-skills-list">
            {job.missing_skills.map((s, i) => (
              <span key={i} className="skill-chip">{s}</span>
            ))}
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="job-card-actions">
        {applyUrl && (
          <a
            href={applyUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn-primary btn-sm"
          >
            View Job <ExternalLinkIcon />
          </a>
        )}
        <button
          className={`btn btn-secondary btn-sm${showBreakdown ? ' active' : ''}`}
          onClick={() => {
            setShowBreakdown((prev) => !prev);
            if (showAssist) setShowAssist(false);
          }}
        >
          {showBreakdown ? 'Hide Details' : 'Score Details'}
        </button>
        <button
          className={`btn btn-secondary btn-sm${showAssist ? ' active' : ''}`}
          onClick={() => {
            setShowAssist((prev) => !prev);
            if (showBreakdown) setShowBreakdown(false);
          }}
          title="Generate cover letter or resume tips for this job"
        >
          ✦ AI Assist
        </button>
      </div>

      {/* Score breakdown (expandable) */}
      {showBreakdown && (
        <ScoreBreakdown breakdown={job.score_breakdown} totalScore={job.score} />
      )}

      {/* AI Assist panel (expandable) */}
      {showAssist && (
        <AssistPanel job={job} onClose={() => setShowAssist(false)} />
      )}
    </div>
  );
}

export default JobCard;
