import { useState } from 'react';
import axios from 'axios';

function UploadResumes() {
  const [code, setCode] = useState('');
  const [files, setFiles] = useState([]);
  const [uploadedResumes, setUploadedResumes] = useState([]);

const handleUpload = async (e) => {
  e.preventDefault();
  if (!files.length || !code) return alert("Please enter code and select files");

  const file = files[0]; // Only handling one file for now
  const reader = new FileReader();

  reader.onload = async () => {
    try {
      const base64String = reader.result.split(",")[1]; // remove prefix

      const payload = {
        filename: file.name,
        jobCode: code,
        fileData: {
          $binary: {
            base64: base64String,
            subType: "00"
          }
        }
      };

      await axios.post("http://localhost:4000/api/resumes/uploadResume", payload, {
        headers: {
          "Content-Type": "application/json"
        }
      });

      alert("Uploaded!");
      setFiles([]);
    } catch (err) {
      console.error("Upload error:", err);
      alert("Failed to upload");
    }
  };

  reader.onerror = (err) => {
    console.error("File read error:", err);
    alert("Error reading file");
  };

  reader.readAsDataURL(file); // This ensures base64 string
};


  const getUpload = async (e) => {
    e.preventDefault();
    if (!code) return alert("Enter a job code");

    try {
      const res = await axios.get(`http://localhost:4000/api/resumes?code=${code}`);
      setUploadedResumes(res.data);
    } catch (err) {
      console.error("Fetch error:", err);
      alert("Could not fetch resumes");
    }
  };

  return (
    <div className="p-4 bg-gray-100 min-h-screen">
      <h1 className="text-xl font-bold mb-4">Upload Resumes with Code</h1>
      <form onSubmit={handleUpload} className="space-y-4 mb-6">
        <input
          type="text"
          placeholder="Enter Code (e.g., ml-2024)"
          value={code}
          onChange={(e) => setCode(e.target.value)}
          className="border px-2 py-1"
        />
        <input
          type="file"
          multiple
          onChange={(e) => setFiles(e.target.files)}
          className="block"
        />
        <button
          type="submit"
          className="bg-green-600 text-white px-4 py-2 rounded"
        >
          Upload
        </button>
      </form>

      <hr className="my-6" />

      <form onSubmit={getUpload} className="space-y-4 mb-4">
        <h2 className="text-xl font-bold">Fetch Resumes for Code</h2>
        <input
          type="text"
          placeholder="Enter Code (e.g., ml-2024)"
          value={code}
          onChange={(e) => setCode(e.target.value)}
          className="border px-2 py-1"
        />
        <button
          type="submit"
          className="bg-blue-600 text-white px-4 py-2 rounded"
        >
          Fetch Resumes
        </button>
      </form>

      <div className="bg-white p-4 rounded shadow-md">
        <h3 className="text-lg font-semibold mb-2">Resumes for "{code}"</h3>
        <ul>
          {uploadedResumes.map((resume, index) => (
            <li key={index}>
              📄 {resume.filename}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

export default UploadResumes;
