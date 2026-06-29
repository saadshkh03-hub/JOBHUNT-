import React, { useState, useCallback } from 'react';
import Header from './components/Header';
import SearchForm from './components/SearchForm';
import Results from './components/Results';
import LoadingState from './components/LoadingState';
import { searchJobs, exportCsv } from './api';

const MAX_RECENT_SEARCHES = 5;

function App() {
  const [step, setStep] = useState(1);
  const [resumeFile, setResumeFile] = useState(null);
  const [searchResults, setSearchResults] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('strong');
  const [recentSearches, setRecentSearches] = useState([]);
  const [isExporting, setIsExporting] = useState(false);

  const handleSearch = async (file, searchParams) => {
    setIsLoading(true);
    setError(null);
    setResumeFile(file);

    try {
      const results = await searchJobs(file, searchParams);
      setSearchResults(results);
      setStep(2);
      setActiveTab('strong');

      // Save to recent searches (in-memory only, session-scoped)
      const entry = {
        id: Date.now(),
        job_title: searchParams.job_title,
        location: searchParams.location,
        work_type: searchParams.work_type,
        timestamp: new Date().toLocaleTimeString('en-AU', { hour: '2-digit', minute: '2-digit' }),
        strongCount: results.strong_matches?.length ?? 0,
        similarCount: results.similar_jobs?.length ?? 0,
        file,
        searchParams,
      };
      setRecentSearches((prev) => [entry, ...prev].slice(0, MAX_RECENT_SEARCHES));
    } catch (err) {
      console.error('Search error:', err);
      if (err.response) {
        const detail = err.response.data?.detail || err.response.statusText;
        setError(`Search failed: ${detail}`);
      } else if (err.code === 'ECONNABORTED') {
        setError('Request timed out — the search is taking too long. Try again.');
      } else if (err.message && err.message.includes('Network Error')) {
        setError('Cannot connect to the backend. Make sure it is running on http://localhost:8000.');
      } else {
        setError(`Search failed: ${err.message}`);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleBack = () => {
    setStep(1);
    setSearchResults(null);
    setError(null);
  };

  const handleRepeatSearch = useCallback((entry) => {
    if (entry.file && entry.searchParams) {
      handleSearch(entry.file, entry.searchParams);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleExportCsv = async () => {
    if (!searchResults) return;
    setIsExporting(true);
    try {
      const allJobs = [
        ...(searchResults.strong_matches || []),
        ...(searchResults.similar_jobs || []),
      ];
      await exportCsv(allJobs);
    } catch (err) {
      console.error('Export error:', err);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="page-wrapper">
      <Header />
      <main className="main-content">
        <div className="container">
          {isLoading && <LoadingState sourcesCount={4} />}

          {!isLoading && step === 1 && (
            <SearchForm
              onSearch={handleSearch}
              error={error}
              recentSearches={recentSearches}
              onRepeatSearch={handleRepeatSearch}
            />
          )}

          {!isLoading && step === 2 && searchResults && (
            <Results
              results={searchResults}
              onBack={handleBack}
              activeTab={activeTab}
              onTabChange={setActiveTab}
              onExportCsv={handleExportCsv}
              isExporting={isExporting}
              candidateProfile={null}
            />
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
