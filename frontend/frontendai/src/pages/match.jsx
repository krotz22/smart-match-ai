import { useEffect, useState } from 'react';
import axios from 'axios';

function SmartMatchPage() {
  const [jobCodes, setJobCodes] = useState([]);
  const [selectedCode, setSelectedCode] = useState('');
  const [resumes, setResumes] = useState([]);
  const [results, setResults] = useState([]);

  useEffect(() => {
    axios.get("http://localhost:4000/api/jobs").then(res => {
      setJobCodes(res.data.map(job => job.jobCode));
    });
  }, []);

  const handleFetchResumes = async () => {
    const res = await axios.get(`http://localhost:4000/api/resumes?code=${selectedCode}`);
    setResumes(res.data);
    setResults([]);
  };

  const handleSmartMatch = async () => {
    try {
      await axios.post(`http://localhost:8000/match/${selectedCode}`);
      const res = await axios.get(`http://localhost:8000/shortlist/${selectedCode}`);
      setResults(res.data);
    } catch (err) {
      console.error("❌ Matching or fetching failed", err);
      alert("Matching or fetching failed");
    }
  };

  return (
    <div className="p-6 bg-gray-100 min-h-screen">
      <h2 className="text-2xl font-bold mb-4">Smart Matching</h2>

      <div className="mb-4">
        <label className="mr-2">Select Job Code:</label>
        <select
          value={selectedCode}
          onChange={(e) => setSelectedCode(e.target.value)}
          className="border px-2 py-1"
        >
          <option value="">-- Select --</option>
          {jobCodes.map((code, index) => (
            <option key={index} value={code}>{code}</option>
          ))}
        </select>
        <button
          onClick={handleFetchResumes}
          className="ml-4 bg-blue-600 text-white px-4 py-2 rounded"
        >
          Fetch Resumes
        </button>
      </div>

      <h3 className="text-xl font-semibold mb-2">Resumes</h3>
      <ul className="mb-4 bg-white p-4 rounded shadow">
        {resumes.map((res, idx) => (
          <li key={idx} className="mb-2">📄 {res.filename}</li>
        ))}
      </ul>

      {resumes.length > 0 && (
        <button
          onClick={handleSmartMatch}
          className="bg-green-600 text-white px-6 py-2 rounded hover:bg-green-700"
        >
          Match with AI
        </button>
      )}

      {results.length > 0 && (
        <div className="mt-6">
          <h3 className="text-xl font-semibold mb-2">Matching Results</h3>
          {results.map((res, i) => (
            <div key={i} className="border p-4 mb-4 bg-white shadow">
              <p><strong>Candidate:</strong> {res.candidateName}</p>
              <p><strong>Score:</strong> {res.score}%</p>
              <p><strong>Matched Skills:</strong> {res.matchedSkills.join(', ')}</p>
              <p><strong>Missing Skills:</strong> {res.missingSkills.join(', ')}</p>
              <p><strong>Shortlisted:</strong> {res.shortlist ? "✅ Yes" : "❌ No"}</p>
              <p className="text-sm text-gray-600 mt-2"><em>{res.summary}</em></p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default SmartMatchPage;