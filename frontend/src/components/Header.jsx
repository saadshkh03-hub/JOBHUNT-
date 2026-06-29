import React from 'react';

function Header() {
  return (
    <header className="header">
      <div className="container">
        <div className="header-inner">
          <div className="header-logo">
            <div className="header-logo-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <rect x="2" y="7" width="20" height="14" rx="2" ry="2"/>
                <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>
              </svg>
            </div>
            <div>
              <h1 className="header-title">Resume Job Matcher AU</h1>
              <p className="header-tagline">Find jobs you are genuinely qualified for</p>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}

export default Header;
