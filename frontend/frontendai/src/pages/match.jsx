import { useEffect, useState } from 'react';
import axios from 'axios';

function SmartMatchPage() {
  const [jobCodes, setJobCodes] = useState([]);
  const [selectedCode, setSelectedCode] = useState('');
  const [resumes, setResumes] = useState([]);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchJobCodes = async () => {
      try {
        const res = await axios.get("https://smart-match-ai-node.onrender.com/api/jobs");
        if (res.data && res.data.jobs) {
          setJobCodes(res.data.jobs.map(job => job.jobCode));
        } else if (Array.isArray(res.data)) {
          setJobCodes(res.data.map(job => job.jobCode));
        }
      } catch (err) {
        console.error("Failed to fetch job codes:", err);
        setError("Failed to fetch job codes");
      }
    };

    fetchJobCodes();
  }, []);

  const handleFetchResumes = async () => {
    if (!selectedCode) {
      alert("Please select a job code first");
      return;
    }

    setLoading(true);
    setError('');
    
    try {
      const res = await axios.get(`https://smart-match-ai-node.onrender.com/api/resumes?code=${selectedCode}`);
      if (res.data && res.data.resumes) {
        setResumes(res.data.resumes);
      } else if (Array.isArray(res.data)) {
        setResumes(res.data);
      } else {
        setResumes([]);
      }
      setResults([]); // Clear previous results
    } catch (err) {
      console.error("Failed to fetch resumes:", err);
      setError("Failed to fetch resumes");
      setResumes([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSmartMatch = async () => {
    if (!selectedCode) {
      alert("Please select a job code first");
      return;
    }

    setLoading(true);
    setError('');

    try {
      console.log("Starting matching process for job code:", selectedCode);
      
      // Step 1: Trigger the matching process
<<<<<<< HEAD
      const matchResponse = await axios.post(`https://smart-match-ai.onrender.com/match/${selectedCode}`);
=======
    const matchResponse = await axios.post(`https://smart-match-ai.onrender.com/match/${selectedCode}`);
>>>>>>> 0dd883b06c413697c33b3425a5f26cd57a965483

// Wait 3 seconds before fetching results
await new Promise(resolve => setTimeout(resolve, 3000));

const shortlistResponse = await axios.get(
  `https://smart-match-ai-node.onrender.com/api/shortlists?code=${selectedCode}` );


      
      // Based on your data structure, handle the response
      let resultsList = [];
      
      if (shortlistResponse.data) {
        if (shortlistResponse.data.shortlist && Array.isArray(shortlistResponse.data.shortlist)) {
          // If the response has a 'shortlist' property containing an array
          resultsList = shortlistResponse.data.shortlist;
        } else if (Array.isArray(shortlistResponse.data)) {
          // If the response is directly an array
          resultsList = shortlistResponse.data;
        } else {
          console.warn("Unexpected response structure:", shortlistResponse.data);
        }
      }
      
      console.log("Final results list:", resultsList);
      setResults(resultsList);
      
      if (resultsList.length === 0) {
        setError("No shortlist results found.");
      }
      
    } catch (err) {
      console.error("Matching or fetching failed:", err);
      if (err.response) {
        setError(`Error: ${err.response.status} - ${err.response.data?.detail || 'Unknown error'}`);
      } else {
        setError("Matching or fetching failed: " + err.message);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 bg-gray-100 min-h-screen">
      <h2 className="text-2xl font-bold mb-4">Smart Matching</h2>

      {error && (
        <div className="mb-4 p-3 bg-red-100 border border-red-300 text-red-700 rounded">
          {error}
        </div>
      )}

      <div className="mb-4">
        <label className="mr-2">Select Job Code:</label>
        <select
          value={selectedCode}
          onChange={(e) => setSelectedCode(e.target.value)}
          className="border px-2 py-1 mr-4"
          disabled={loading}
        >
          <option value="">-- Select --</option>
          {jobCodes.map((code, index) => (
            <option key={index} value={code}>{code}</option>
          ))}
        </select>
        <button
          onClick={handleFetchResumes}
          disabled={loading || !selectedCode}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:bg-gray-400"
        >
          {loading ? "Loading..." : "Fetch Resumes"}
        </button>
      </div>

      <h3 className="text-xl font-semibold mb-2">
        Resumes {resumes.length > 0 && `(${resumes.length})`}
      </h3>
      <ul className="mb-4 bg-white p-4 rounded shadow">
        {resumes.length === 0 ? (
          <li className="text-gray-500">No resumes found for this job code</li>
        ) : (
          resumes.map((res, idx) => (
            <li key={idx} className="mb-2">
              📄 {res.filename || res.candidateName || `Resume ${idx + 1}`}
            </li>
          ))
        )}
      </ul>

      {resumes.length > 0 && (
        <button
          onClick={handleSmartMatch}
          disabled={loading}
          className="bg-green-600 text-white px-6 py-2 rounded hover:bg-green-700 disabled:bg-gray-400"
        >
          {loading ? "Processing..." : "Match with AI"}
        </button>
      )}

      {/* Results Section - This should now work! */}
      {results.length > 0 && (
        <div className="mt-6">
          <h3 className="text-xl font-semibold mb-2">
            Matching Results ({results.length} candidates)
          </h3>
          {results.map((res, i) => (
            <div key={res._id || i} className="border p-4 mb-4 bg-white shadow rounded">
              <p><strong>Candidate:</strong> {res.candidateName || 'N/A'}</p>
              <p><strong>Score:</strong> {res.score || 0}%</p>
              <p><strong>Matched Skills:</strong> {
                res.matchedSkills && res.matchedSkills.length > 0 
                  ? res.matchedSkills.join(', ') 
                  : 'None'
              }</p>
              <p><strong>Missing Skills:</strong> {
                res.missingSkills && res.missingSkills.length > 0 
                  ? res.missingSkills.join(', ') 
                  : 'None'
              }</p>
              <p><strong>Shortlisted:</strong> 
                <span className={res.shortlist ? "text-green-600 ml-2" : "text-red-600 ml-2"}>
                  {res.shortlist ? "✅ Yes" : "❌ No"}
                </span>
              </p>
              <p className="text-sm text-gray-600 mt-2">
                <em>{res.summary || 'No summary available'}</em>
              </p>
              {res.dateShortlisted && (
                <p className="text-xs text-gray-500 mt-1">
                  Processed: {new Date(res.dateShortlisted).toLocaleString()}
                </p>
              )}
            </div>
          ))}
        </div>
      )}

      {loading && (
        <div className="mt-4 text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2">Processing...</p>
        </div>
      )}
    </div>
  );
}

export default SmartMatchPage;
