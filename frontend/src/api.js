import axios from 'axios';

const BASE_URL = '';  // uses CRA proxy to http://localhost:8000

/**
 * Parse a resume file and return a CandidateProfile.
 * @param {File} file
 * @returns {Promise<Object>} CandidateProfile
 */
export async function parseResume(file) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await axios.post(`${BASE_URL}/api/resume/parse`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
}

/**
 * Search for jobs using the resume and search parameters.
 * @param {File} file - Resume file
 * @param {Object} searchParams - Search parameters matching SearchRequest model
 * @returns {Promise<Object>} SearchResponse
 */
export async function searchJobs(file, searchParams) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('job_title', searchParams.job_title || '');
  formData.append('location', searchParams.location || '');
  formData.append('radius_km', String(searchParams.radius_km || 50));
  formData.append('work_type', searchParams.work_type || 'any');
  formData.append('job_source_filter', searchParams.job_source_filter || 'all');
  formData.append('min_score', String(searchParams.min_score || 40));
  formData.append('strong_match_threshold', String(searchParams.strong_match_threshold || 70));
  formData.append('min_strong_matches', String(searchParams.min_strong_matches || 5));

  const response = await axios.post(`${BASE_URL}/api/search`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000,  // 60s for search (multiple external APIs)
  });
  return response.data;
}

/**
 * Health check
 * @returns {Promise<Object>}
 */
export async function healthCheck() {
  const response = await axios.get(`${BASE_URL}/api/health`);
  return response.data;
}
