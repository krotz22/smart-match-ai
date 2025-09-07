const mongoose = require("mongoose");

const shortlistSchema = new mongoose.Schema({
  candidateName: String,
  jobCode: String,
  score: Number,
  matchedSkills: [String],
  missingSkills: [String],
  summary: String,
  email: { type: String, default: "N/A" }, 
  dateShortlisted: { type: Date, default: Date.now },
});

// Prevent model overwrite error during hot reload
module.exports =
  mongoose.models.Shortlist || mongoose.model("Shortlist", shortlistSchema);
