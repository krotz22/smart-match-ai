const mongoose = require('mongoose');

const resumeSchema = new mongoose.Schema({
  filename: String,
  jobCode: String,
  fileData: Buffer,  // 🔥 This field is CRUCIAL
  contentType: String,
  uploadDate: {
    type: Date,
    default: Date.now
  }
});

module.exports = mongoose.model('Resume', resumeSchema);
