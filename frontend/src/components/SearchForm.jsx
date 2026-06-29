import React, { useState, useRef, useCallback } from 'react';

const RADIUS_OPTIONS = [
  { value: 10, label: '10 km' },
  { value: 25, label: '25 km' },
  { value: 50, label: '50 km' },
  { value: 100, label: '100 km' },
  { value: 500, label: 'Australia-wide' },
];

function SearchForm({ onSearch, error }) {
  const [file, setFile] = useState(null);
  const [jobTitle, setJobTitle] = useState('');
  const [location, setLocation] = useState('');
  const [radiusKm, setRadiusKm] = useState(50);
  const [workType, setWorkType] = useState('any');
  const [sourceFilter, setSourceFilter] = useState('all');
  const [minScore, setMinScore] = useState(40);
  const [isDragging, setIsDragging] = useState(false);
  const [validationErrors, setValidationErrors] = useState({});
  const fileInputRef = useRef(null);

  const validate = () => {
    const errs = {};
    if (!file) errs.file = 'Please upload your resume (PDF, DOCX, or TXT)';
    if (!jobTitle.trim()) errs.jobTitle = 'Please enter a job title or keywords';
    return errs;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length > 0) {
      setValidationErrors(errs);
      return;
    }
    setValidationErrors({});
    onSearch(file, {
      job_title: jobTitle.trim(),
      location: location.trim(),
      radius_km: radiusKm,
      work_type: workType,
      job_source_filter: sourceFilter,
      min_score: minScore,
      strong_match_threshold: 70,
      min_strong_matches: 5,
    });
  };

  const handleFileChange = (selectedFile) => {
    if (!selectedFile) return;
    const allowed = ['application/pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'application/msword', 'text/plain'];
    const ext = selectedFile.name.toLowerCase();
    if (!allowed.includes(selectedFile.type) && !ext.endsWith('.pdf') && !ext.endsWith('.docx') && !ext.endsWith('.txt')) {
      setValidationErrors(prev => ({ ...prev, file: 'Only PDF, DOCX, or TXT files are supported' }));
      return;
    }
    setFile(selectedFile);
    setValidationErrors(prev => { const e = { ...prev }; delete e.file; return e; });
  };

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped) handleFileChange(dropped);
  }, []);

  const handleDragOver = (e) => { e.preventDefault(); setIsDragging(true); };
  const handleDragLeave = () => setIsDragging(false);

  const areaClass = ['file-upload-area', isDragging ? 'drag-over' : '', file ? 'has-file' : ''].filter(Boolean).join(' ');

  return (
    <div>
      <div style={{ marginBottom: '1.5rem' }}>
        <h2 style={{ fontSize: '1.375rem', marginBottom: '0.25rem' }}>Find your next role</h2>
        <p style={{ color: 'var(--text-light)', fontSize: '0.9375rem' }}>
          Upload your resume and we will match you to jobs based on your actual skills and experience.
        </p>
      </div>

      {error && (
        <div className="error-banner" role="alert">
          <strong>Error: </strong>{error}
        </div>
      )}

      <form onSubmit={handleSubmit} noValidate>
        {/* File upload */}
        <div className="form-group">
          <label className="form-label">Resume <span style={{ color: 'var(--error)' }}>*</span></label>
          <div
            className={areaClass}
            onClick={() => fileInputRef.current?.click()}
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => e.key === 'Enter' && fileInputRef.current?.click()}
            aria-label="Upload resume file"
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.docx,.doc,.txt"
              style={{ display: 'none' }}
              onChange={(e) => handleFileChange(e.target.files?.[0])}
            />
            <div className="file-upload-icon">
              {file ? (
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--success)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                  <polyline points="22 4 12 14.01 9 11.01"/>
                </svg>
              ) : (
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--text-light)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                  <polyline points="17 8 12 3 7 8"/>
                  <line x1="12" y1="3" x2="12" y2="15"/>
                </svg>
              )}
            </div>
            {file ? (
              <div>
                <p className="file-upload-title file-upload-selected">{file.name}</p>
                <p className="file-upload-hint">Click to change file</p>
              </div>
            ) : (
              <div>
                <p className="file-upload-title">Drag &amp; drop your resume here</p>
                <p className="file-upload-hint">or click to browse — PDF, DOCX, or TXT</p>
              </div>
            )}
          </div>
          {validationErrors.file && <p className="form-error">{validationErrors.file}</p>}
        </div>

        {/* Job title + location */}
        <div className="search-form-grid">
          <div className="form-group">
            <label className="form-label" htmlFor="jobTitle">
              Job Title / Keywords <span style={{ color: 'var(--error)' }}>*</span>
            </label>
            <input
              id="jobTitle"
              type="text"
              className={`form-input${validationErrors.jobTitle ? ' error' : ''}`}
              placeholder="e.g. Software Engineer, Policy Officer"
              value={jobTitle}
              onChange={(e) => {
                setJobTitle(e.target.value);
                if (validationErrors.jobTitle) setValidationErrors(p => { const e = {...p}; delete e.jobTitle; return e; });
              }}
            />
            {validationErrors.jobTitle && <p className="form-error">{validationErrors.jobTitle}</p>}
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="location">Location</label>
            <input
              id="location"
              type="text"
              className="form-input"
              placeholder="e.g. Sydney, Melbourne, Canberra"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
            />
            <p className="form-hint">Leave blank to search Australia-wide</p>
          </div>

          {/* Radius */}
          <div className="form-group">
            <label className="form-label" htmlFor="radius">
              Search Radius: <span className="range-value">{radiusKm >= 500 ? 'Australia-wide' : `${radiusKm} km`}</span>
            </label>
            <select
              id="radius"
              className="form-select"
              value={radiusKm}
              onChange={(e) => setRadiusKm(Number(e.target.value))}
            >
              {RADIUS_OPTIONS.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>

          {/* Work type */}
          <div className="form-group">
            <label className="form-label" htmlFor="workType">Work Arrangement</label>
            <select
              id="workType"
              className="form-select"
              value={workType}
              onChange={(e) => setWorkType(e.target.value)}
            >
              <option value="any">Any arrangement</option>
              <option value="remote">Remote</option>
              <option value="hybrid">Hybrid</option>
              <option value="onsite">On-site</option>
            </select>
          </div>

          {/* Source filter */}
          <div className="form-group">
            <label className="form-label" htmlFor="sourceFilter">Job Sources</label>
            <select
              id="sourceFilter"
              className="form-select"
              value={sourceFilter}
              onChange={(e) => setSourceFilter(e.target.value)}
            >
              <option value="all">All sources</option>
              <option value="government">Government (APS) only</option>
              <option value="council">Council only</option>
            </select>
          </div>

          {/* Min score */}
          <div className="form-group">
            <label className="form-label" htmlFor="minScore">
              Minimum match score: <span className="range-value">{minScore}%</span>
            </label>
            <input
              id="minScore"
              type="range"
              className="form-range"
              min="0"
              max="90"
              step="5"
              value={minScore}
              onChange={(e) => setMinScore(Number(e.target.value))}
            />
            <div className="range-labels">
              <span>Show all</span>
              <span>Strong only</span>
            </div>
          </div>
        </div>

        <div style={{ marginTop: '0.5rem' }}>
          <button type="submit" className="btn btn-primary btn-lg">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="11" cy="11" r="8"/>
              <line x1="21" y1="21" x2="16.65" y2="16.65"/>
            </svg>
            Search Jobs
          </button>
        </div>
      </form>
    </div>
  );
}

export default SearchForm;
