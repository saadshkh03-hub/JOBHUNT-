import React from 'react';

const DIMENSIONS = [
  { key: 'title_relevance',     label: 'Title Relevance',       weight: 20 },
  { key: 'skills_overlap',      label: 'Skills Match',          weight: 25 },
  { key: 'preferred_skills',    label: 'Preferred Skills',      weight: 10 },
  { key: 'seniority_alignment', label: 'Seniority Alignment',   weight: 10 },
  { key: 'industry_relevance',  label: 'Industry Relevance',    weight: 10 },
  { key: 'location_fit',        label: 'Location Fit',          weight: 10 },
  { key: 'work_type_fit',       label: 'Work Type Fit',         weight: 5  },
  { key: 'eligibility_fit',     label: 'Eligibility Fit',       weight: 5  },
  { key: 'transferable_skills', label: 'Transferable Skills',   weight: 5  },
];

function ScoreBreakdown({ breakdown, totalScore }) {
  if (!breakdown) return null;

  return (
    <div className="score-breakdown">
      <div className="score-breakdown-title">
        Score Breakdown — Total: {totalScore}%
      </div>
      {DIMENSIONS.map(({ key, label, weight }) => {
        const rawScore = breakdown[key] ?? 0;
        const weighted = ((rawScore * weight) / 100).toFixed(1);
        return (
          <div key={key} className="breakdown-row">
            <span className="breakdown-label" title={`Weight: ${weight}%`}>{label}</span>
            <div className="breakdown-bar-track">
              <div
                className="breakdown-bar-fill"
                style={{ width: `${rawScore}%` }}
              />
            </div>
            <span className="breakdown-value" title={`Raw: ${rawScore} × ${weight}% = ${weighted}`}>
              {weighted}
            </span>
          </div>
        );
      })}
      <p style={{ fontSize: '0.75rem', color: 'var(--text-light)', marginTop: '0.5rem', marginBottom: 0 }}>
        Values show weighted contribution to total score. Hover for details.
      </p>
    </div>
  );
}

export default ScoreBreakdown;
