const mongoose = require("mongoose");

const resumeSchema = new mongoose.Schema({
  filename: String,
  jobCode: String,
  fileData: Buffer,        // Optional: if storing file content in DB
  contentType: String,     // Optional: file MIME type
  uploadDate: { type: Date, default: Date.now },
});

// ✅ Use existing model if already compiled
module.exports = mongoose.models.Resume || mongoose.model("Resume", resumeSchema);
