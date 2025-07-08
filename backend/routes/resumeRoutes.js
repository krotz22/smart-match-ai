// resumeRoutes.js
const express = require("express");
const router = express.Router();
const multer = require("multer");
const path = require("path");
const Resume = require("../models/Resume");

const Buffer = require("buffer").Buffer;

// POST endpoint to store base64 PDF into MongoDB
router.post("/uploadResume", async (req, res) => {
  try {
    const { filename, jobCode, fileData } = req.body;

    if (!fileData?.$binary?.base64) {
      return res.status(400).json({ error: "Missing file data" });
    }

    const base64String = fileData.$binary.base64;

    // Decode base64 to binary
    const pdfBuffer = Buffer.from(base64String, "base64");

    const resume = new Resume({
      filename,
      jobCode,
      file: pdfBuffer,
      contentType: "application/pdf"
    });

    await resume.save();

    res.status(201).json({ message: "Resume saved successfully" });
  } catch (err) {
    console.error("Error saving resume:", err);
    res.status(500).json({ error: "Internal Server Error" });
  }
});

// Get resumes by jobCode
router.get("/", async (req, res) => {
  console.log("Query params:", req.query);  // 👈 debug
  const { code } = req.query;
  const resumes = await Resume.find({ jobCode: code });
  res.json(resumes);
});

module.exports = router;
