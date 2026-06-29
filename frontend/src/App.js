import React, { useState } from 'react';
import Header from './components/Header';
import SearchForm from './components/SearchForm';
import Results from './components/Results';
import LoadingState from './components/LoadingState';
import { searchJobs } from './api';

function App() {
  const [step, setStep] = useState(1);
  const [resumeFile, setResumeFile] = useState(null);
  const [searchResults, setSearchResults] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('strong');

  const handleSearch = async (file, searchParams) => {
    setIsLoading(true);
    setError(null);
    setResumeFile(file);

    try {
      const results = await searchJobs(file, searchParams);
      setSearchResults(results);
      setStep(2);
      setActiveTab('strong');
    } catch (err) {
      console.error('Search error:', err);
      if (err.response) {
        const detail = err.response.data?.detail || err.response.statusText;
        setError(`Search failed: ${detail}`);
      } else if (err.code === 'ECONNABORTED') {
        setError('Request timed out. The search is taking too long — try again.');
      } else if (err.message.includes('Network Error')) {
        setError('Cannot connect to the backend server. Make sure it is running on http://localhost:8000.');
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

  return (
    <div className="page-wrapper">
      <Header />
      <main className="main-content">
        <div className="container">
          {isLoading && (
            <LoadingState
              sourcesCount={3}
            />
          )}
          {!isLoading && step === 1 && (
            <SearchForm
              onSearch={handleSearch}
              error={error}
            />
          )}
          {!isLoading && step === 2 && searchResults && (
            <Results
              results={searchResults}
              onBack={handleBack}
              activeTab={activeTab}
              onTabChange={setActiveTab}
            />
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
