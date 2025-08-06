import { useState, useEffect } from "react";
import axios from "axios";

function JobsPage() {
  const [jobs, setJobs] = useState([]);
  const [newTitle, setNewTitle] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [newCode, setNewCode] = useState("");
  const [showForm, setShowForm] = useState(false);

  // Fetch jobs on mount
  useEffect(() => {
    fetchJobs();
  }, []);

  const fetchJobs = async () => {
    const res = await axios.get("https://smart-match-ai-node.onrender.com/api/jobs");
    setJobs(res.data);
  };

  const handleAddJob = async () => {
    if (!newTitle || !newDesc || !newCode) return;
    const res = await axios.post("https://smart-match-ai-node.onrender.com/api/jobs", {
      title: newTitle,
      description: newDesc,
      jobCode: newCode,
    });
    setJobs([res.data.job, ...jobs]);
    setNewTitle("");
    setNewDesc("");
    setNewCode("");
    setShowForm(false);
  };

  const handleDeleteJob = async (id) => {
    await axios.delete(`https://smart-match-ai-node.onrender.com/api/jobs/${id}`);
    setJobs(jobs.filter((job) => job._id !== id));
  };

  return (
    <section className="p-6 bg-gray-100 min-h-screen">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-3xl font-semibold">Available Job Descriptions</h2>
        <button
          className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
          onClick={() => setShowForm(!showForm)}
        >
          {showForm ? "Close" : "Add Job"}
        </button>
      </div>

      {showForm && (
        <div className="bg-white p-4 rounded shadow-md mb-6">
          <input
            type="text"
            placeholder="Job Title"
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            className="border p-2 w-full mb-2"
          />
          <textarea
            placeholder="Job Description"
            value={newDesc}
            onChange={(e) => setNewDesc(e.target.value)}
            className="border p-2 w-full mb-2"
          />
          <input
            type="text"
            placeholder="Job Code"
            value={newCode}
            onChange={(e) => setNewCode(e.target.value)}
            className="border p-2 w-full mb-2"
          />
          <button
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
            onClick={handleAddJob}
          >
            Save Job
          </button>
        </div>
      )}

      <div className="flex flex-col space-y-4 overflow-y-auto p-2">
        {jobs.map((job) => (
          <div key={job._id} className="min-w-[250px] bg-white p-4 rounded shadow-md">
            <h3 className="text-xl font-bold">{job.title}</h3>
            <p className="text-gray-600">{job.description}</p>
            <h4 className="font-bold mt-2">Job Code: {job.jobCode}</h4>
            <div className="flex justify-between mt-4">
              <button className="bg-green-600 text-white px-6 py-2 rounded hover:bg-green-700">
                Recruit
              </button>
              <button
                onClick={() => handleDeleteJob(job._id)}
                className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"
              >
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

export default JobsPage;
